try:
    import unzip_requirements
except ImportError:
    pass

import json

from irs_lookup.util import JsonDecimalEncoder
from irs_lookup import lookup_aws
from irs_lookup import lookup_irs
from irs_lookup import ingest


def fetch_990(event, context):
    if event is not None and \
            "pathParameters" in event and \
            event["pathParameters"] is not None and \
            "ein" in event["pathParameters"]:

        source = None
        if "queryStringParameters" in event and \
                event["queryStringParameters"] is not None and \
                "source" in event["queryStringParameters"]:
            source = event["queryStringParameters"]["source"]

        if source is not None and source == "irs":
            df = lookup_irs.lookup_990s([event["pathParameters"]["ein"]])
        else:
            df = lookup_aws.lookup_990s([event["pathParameters"]["ein"]])

        df.reset_index(drop=True, inplace=True)
        response_body = json.dumps(df.to_dict('records'), cls=JsonDecimalEncoder)

        response = {
            "statusCode": 200,
            "body": response_body
        }
        return response


def refresh_990s_bkgd(event, context):
    if event is not None:
        body = json.loads(event['body'])

        year = None
        if 'year' in body:
            year = body['year']
        ingest.refresh_990s(year=year)


if __name__ == "__main__":
    pass
