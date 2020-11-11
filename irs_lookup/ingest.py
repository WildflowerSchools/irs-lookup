import io
import os
import pandas as pd
import requests

from .handle.dynamodb import add_990s, delete_990s_by_year
from .log import logger

START_YEAR = 2016


def load_990s_for_year(year):
    url = "https://s3.amazonaws.com/irs-form-990/index_{}.csv".format(year)
    response = requests.get(url)
    if response.status_code == 404:
        return None
    else:
        return response.content


def refresh_990s(year=None):
    ein_filter = os.environ.get('EIN_FILTER', [])
    if not isinstance(ein_filter, list):
        ein_filter = ein_filter.split(',')
        ein_filter = [int(v) for v in ein_filter]

    all_years = year is None

    current_year = START_YEAR
    if year is not None:
        current_year = int(year)

    while True:
        logger.info("Importing records for {}".format(current_year))
        d = load_990s_for_year(current_year)
        if d is None:
            logger.info("Records not found for {}".format(current_year))
            break

        logger.info("Removing old records for {}".format(current_year))
        delete_990s_by_year(current_year)

        returns_df = pd.read_csv(io.StringIO(d.decode('utf-8')))
        returns_df = returns_df.rename(columns={
            "RETURN_ID": "id",
            "EIN": "ein",
            "SUB_DATE": "sub_date",
            "FILING_TYPE": "filing_type",
            "TAX_PERIOD": "tax_period",
            "OBJECT_ID": "object_id",
            "DLN": "dln",
            "RETURN_TYPE": "return_type",
            "TAXPAYER_NAME": "taxpayer_name"})

        returns_df.id = returns_df.id.astype(int)
        returns_df.ein = returns_df.ein.astype(int)
        returns_df.tax_period = returns_df.tax_period.astype(str)

        if len(ein_filter) > 0:
            returns_df = returns_df[returns_df['ein'].isin(ein_filter)]

        records = []
        for idx, r in enumerate(returns_df.to_dict('records')):
            records.append(r)

            if (idx % 25) == 0:
                add_990s(records)
                records.clear()
                logger.info(
                    "Imported {}/{}".format(idx, len(returns_df.index)))

        add_990s(records)
        logger.info(
            "Imported {}/{}".format(len(returns_df.index), len(returns_df.index)))
        logger.info("Finished importing records for {}".format(current_year))

        if all_years is False:
            break

        current_year += 1
