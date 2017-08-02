#!/bin/bash
cd $(dirname $(readlink -f $0))
tox -e ddblocal
