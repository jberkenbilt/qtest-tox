# -*- coding: utf-8 -*-
from __future__ import print_function
from contextlib import contextmanager
import os
import sys
import time

from botocore.exceptions import ClientError
import boto3

whoami = os.path.basename(sys.argv[0])
whereami = os.path.dirname(os.path.realpath(__file__))


def warn(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def is_aws_error(e, code):
    return code == e.response['Error']['Code']


@contextmanager
def check_condition():
    try:
        yield
    except ClientError as e:
        if not is_aws_error(e, 'ConditionalCheckFailedException'):
            raise


class Metadata:
    def __init__(self, table, dynamodb_resource_options=None):
        self.table = table
        self.dynamodb_resource_options = (dynamodb_resource_options
                                          if dynamodb_resource_options
                                          else {})
        self.create_table()

    def db(self):
        return boto3.resource('dynamodb', **self.dynamodb_resource_options)

    def create_table(self):
        db = self.db()
        try:
            while ('ACTIVE' != db.Table(self.table).table_status):
                time.sleep(0.1)
            return
        except ClientError as e:
            if is_aws_error(e, 'ResourceNotFoundException'):
                db.create_table(
                    TableName=self.table,
                    AttributeDefinitions=[
                        {'AttributeName': 'key',
                         'AttributeType': 'S'
                         }
                    ],
                    KeySchema=[
                        {'AttributeName': 'key',
                         'KeyType': 'HASH'
                         }
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 1,
                        'WriteCapacityUnits': 1
                    }
                )
            else:
                raise
        while ('ACTIVE' != db.Table(self.table).table_status):
            time.sleep(0.1)

    def add_new(self, key, value):
        with check_condition():
            self.db().Table(self.table).put_item(
                Item={
                    'key': key,
                    'value': value,
                },
                ConditionExpression='attribute_not_exists(#a)',
                ExpressionAttributeNames={'#a': 'key'}
            )
            return True
        return False

    def update(self, key, value, old):
        with check_condition():
            self.db().Table(self.table).put_item(
                Item={
                    'key': key,
                    'value': value,
                },
                ConditionExpression='#a = :v',
                ExpressionAttributeNames={'#a': 'value'},
                ExpressionAttributeValues={':v': old}
            )
            return True
        return False

    def delete(self, key, value):
        with check_condition():
            self.db().Table(self.table).delete_item(
                Key={'key': key},
                ConditionExpression='#a = :v',
                ExpressionAttributeNames={'#a': 'value'},
                ExpressionAttributeValues={':v': value}
            )
            return True
        return False

    def get_all(self):
        scan_args = {'ConsistentRead': True}
        response = self.db().Table(self.table).scan(scan_args)
        return sorted(response['Items'], key=lambda x: x['key'])


class MainClass:
    def main(self):
        print('run the test code')
