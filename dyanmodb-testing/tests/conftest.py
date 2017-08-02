import os
import shutil
import socket
import subprocess
import time
import zipfile

from botocore.exceptions import ClientError
import boto3
import contextlib
import moto
import pytest
import requests

use_moto = True if os.getenv('USE_MOTO') else False  # duplicated
dynamodb_local = True if os.getenv('DYNAMODB_LOCAL') else False

resource_options = {
    'region_name': 'us-west-1',
    'aws_access_key_id': 'access',
    'aws_secret_access_key': 'secret',
}


def get_open_port():
    with contextlib.closing(
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
        return port


def get_ddb_local():
    localdir = pytest.config.rootdir.join('dynamodb-local').strpath
    if not os.path.exists(localdir):
        tempdir = localdir + '.tmp'
        if (os.path.exists(tempdir)):
            shutil.rmtree(tempdir)
        os.mkdir(tempdir)
        r = requests.get(
            'https://s3-us-west-2.amazonaws.com/' +
            'dynamodb-local/dynamodb_local_latest.zip',
            stream=True)
        dist = os.path.join(tempdir, 'dist.zip')
        with open(dist, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        zip_ref = zipfile.ZipFile(dist, 'r')
        zip_ref.extractall(tempdir)
        zip_ref.close()
        os.rename(tempdir, localdir)
    return localdir


def start_dynamodb_local():
    cwd = get_ddb_local()
    port = get_open_port()
    proc = subprocess.Popen(['java', '-Djava.library.path=./DynamoDBLocal_lib',
                             '-jar', 'DynamoDBLocal.jar', '-inMemory',
                             '-port', str(port)], cwd=cwd)
    resource_options['endpoint_url'] = 'http://localhost:{}'.format(port)
    return proc

# Use class-scoped fixtures for dynamodb access Use a
# separate test class for each group of tests that cumulatively update
# dynamodb.


@pytest.fixture(scope='class')
def dynamodb_resource_options():
    if dynamodb_local or use_moto:
        return resource_options
    else:
        return {}


@pytest.fixture(scope='class', autouse=True)
def do_provide_aws():
    if use_moto:
        with moto.mock_dynamodb2():
            yield
    elif dynamodb_local:
        proc = start_dynamodb_local()
        yield
        proc.terminate()
    else:
        yield
        ddb_cleanup()


def ddb_cleanup():
    db = boto3.resource('dynamodb')
    table = table_name()
    try:
        db.Table(table).delete()
        while True:
            db.Table(table).table_status
            time.sleep(1)
    except ClientError:
        pass


@pytest.fixture
def table_name():
    return 'qww_test'
