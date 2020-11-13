import boto3
import botocore
from boto3.dynamodb.conditions import Key
import os

from irs_lookup.log import logger

TABLE_990S = os.environ.get('TABLE_990S')
IS_LOCAL = os.environ.get('IS_LOCAL')
IS_OFFLINE = os.environ.get('IS_OFFLINE')

DEFAULT_PROJECTED_ATTRS = ['id', 'ein', 'year']


def client():
    attrs = dict()
    if IS_LOCAL or IS_OFFLINE:
        endpoint_url = os.environ.get(
            'AWS_ENDPOINT_URL', 'http://localhost:8000')
        attrs['region_name'] = 'localhost'
        attrs['endpoint_url'] = endpoint_url
    else:
        endpoint_url = os.environ.get('AWS_ENDPOINT_URL', None)
        if endpoint_url is not None:
            attrs['endpoint_url'] = endpoint_url

    return boto3.resource('dynamodb', **attrs)


def delete_990s_by_year(year, dynamodb=None):
    if dynamodb is None:
        dynamodb = client()

    try:
        table = dynamodb.Table(TABLE_990S)
        response = table.query(
            IndexName="year-index",
            KeyConditionExpression=Key('year').eq(year))
        records = response['Items']
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey'])
            records += response['Items']

        batchsize = 25
        for ii in range(0, len(records), batchsize):
            batch_items = records[ii:ii + batchsize]
            for item in batch_items:
                with table.batch_writer() as writer:
                    writer.delete_item(Item=item)

    except botocore.exceptions.ClientError as e:
        logger.error(e.response['Error']['Message'])
        logger.error("Failed deleting records for year: {}".format(year))
        raise


def add_990s(records=[], dynamodb=None):
    if dynamodb is None:
        dynamodb = client()

    try:
        table = dynamodb.Table(TABLE_990S)
        with table.batch_writer() as writer:
            for item in records:
                writer.put_item(Item=item)
    except botocore.exceptions.ClientError as e:
        # Ignore the ConditionalCheckFailedException, bubble up
        # other exceptions.
        if e.response['Error']['Code'] != 'ConditionalCheckFailedException':
            logger.error(e.response['Error']['Message'])
            logger.error("Failed inserting: {}".format(records))
            raise
    else:
        return True


def get_990s(key, value, index=None, projected_attrs=None, dynamodb=None):
    if projected_attrs is None:
        projected_attrs = DEFAULT_PROJECTED_ATTRS

    if dynamodb is None:
        dynamodb = client()

    table = dynamodb.Table(TABLE_990S)

    try:
        query_attrs = {'KeyConditionExpression': Key(key).eq(value)}
        if index is not None:
            query_attrs['IndexName'] = index
        if len(projected_attrs) > 0:
            expression_attr_names = {}
            if 'year' in projected_attrs:
                projected_attrs = list(
                    map(lambda p: '#yr' if p == 'year' else p, projected_attrs))
                expression_attr_names['#yr'] = 'year'

            query_attrs['ProjectionExpression'] = ','.join(
                map(lambda a: str(a), projected_attrs))

            if len(expression_attr_names.keys()) > 0:
                query_attrs['ExpressionAttributeNames'] = expression_attr_names

        response = table.query(**query_attrs)
    except botocore.exceptions.ClientError as e:
        logger.error(e.response['Error']['Message'])
    else:
        if 'Item' in response:
            return [response['Item']]
        elif 'Items' in response:
            return response['Items']
        else:
            return []


def get_990s_by_id(_id, projected_attrs=None, dynamodb=None):
    if projected_attrs is None:
        projected_attrs = DEFAULT_PROJECTED_ATTRS
    return get_990s('id', _id, projected_attrs=projected_attrs,
                    dynamodb=dynamodb)


def get_990s_by_ein(ein, projected_attrs=None, dynamodb=None):
    if projected_attrs is None:
        projected_attrs = DEFAULT_PROJECTED_ATTRS
    return get_990s('ein', ein, index='ein-index',
                    projected_attrs=projected_attrs, dynamodb=dynamodb)
