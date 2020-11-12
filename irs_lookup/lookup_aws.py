import dateparser
import pandas as pd
import requests
import traceback
from xml.etree import ElementTree

from irs_lookup.handle.dynamodb import get_990s_by_ein
from irs_lookup.util import is_integer


def load_990(url):
    response = requests.get(url)
    return response.content


def lookup_990s_by_ein(ein):
    ein = ein.strip()

    columns = [
        'ein',
        'name',
        'tax_period',
        'return_id',
        'return_type',
        'filing_name',
        'filing_url',
        'filing_date_start',
        'filing_date_end']
    irs_returns = pd.DataFrame(columns=columns)

    if len(ein) < 9:
        print("EIN must be 9 characters or longer")
        return irs_returns

    if not is_integer(ein):
        print("EIN must be an integer")
        return irs_returns

    ein = int(ein)

    items = get_990s_by_ein(
        ein,
        projected_attrs=[
            'id',
            'ein',
            'year',
            'return_type',
            'tax_period',
            'object_id',
            'taxpayer_name',
            'sub_date'])

    xml_ns = {'': 'http://www.irs.gov/efile'}

    try:
        for item in items:
            xml_url = "https://s3.amazonaws.com/irs-form-990/{}_public.xml".format(
                item['object_id'])
            form_990 = load_990(xml_url)

            r_name, r_tax_period, r_return_id, r_return_type, r_filing_name, r_filing_url, r_filing_date_start, r_filing_date_end = None, None, None, None, None, None, None, None

            root = ElementTree.fromstring(form_990)
            return_header = root.find('ReturnHeader', xml_ns)
            filer_details = return_header.find('Filer', xml_ns)

            r_name = filer_details.find(
                'BusinessName', xml_ns).find(
                'BusinessNameLine1Txt', xml_ns).text
            r_return_id = item['id']
            r_return_type = item['return_type']
            r_tax_period = item['tax_period']
            r_filing_name = item['tax_period']
            r_filing_url = "https://apps.irs.gov/pub/epostcard/cor/{}_{}_{}_{}{}.pdf".format(
                ein,
                item['tax_period'],
                item['return_type'],
                dateparser.parse(item['sub_date']).strftime('%Y%m%d'),
                item['id'])
            r_filing_date_start = return_header.find(
                'TaxPeriodBeginDt', xml_ns).text
            r_filing_date_end = return_header.find(
                'TaxPeriodEndDt', xml_ns).text

            row = pd.DataFrame([[ein,
                                 r_name,
                                 r_tax_period,
                                 r_return_id,
                                 r_return_type,
                                 r_filing_name,
                                 r_filing_url,
                                 r_filing_date_start,
                                 r_filing_date_end]],
                               columns=columns)
            irs_returns = irs_returns.append(row)

            print("Finished {}".format(ein))
    except Exception as err:
        print(ein, 'error')
        traceback.print_exc()

        print(err)

    return irs_returns


def lookup_990s(eins=[]):
    irs_returns = None
    for ein in eins:
        df = lookup_990s_by_ein(ein)
        if df is None:
            continue

        if irs_returns is None:
            irs_returns = df
        else:
            irs_returns = irs_returns.append(df)

    return irs_returns
