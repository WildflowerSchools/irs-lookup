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
        df = lookup_aws.lookup_990s([event["pathParameters"]["ein"]])

        df.reset_index(drop=True, inplace=True)
        response_body = json.dumps(df.to_dict('records'), cls=JsonDecimalEncoder)

        response = {
            "statusCode": 200,
            "body": response_body
        }
        return response


# def refresh_990s_http(event, context):
#     if event is not None:
#         client = boto3_client('lambda')
#         client.invoke(
#             FunctionName='refresh_990s_bkgd',
#             InvocationType='Event',
#             Payload=json.dumps(event)
#         )
#         return {"result": "OK"}


def refresh_990s_bkgd(event, context):
    if event is not None:
        body = json.loads(event['body'])

        year = None
        if 'year' in body:
            year = body['year']
        ingest.refresh_990s(year=year)


if __name__ == "__main__":
    pass
