#!/usr/bin/env bash

. ./vars_refresh.sh

./package_refresh.sh

PYTHONPATH=./dist_refresh:$PYTHONPATH python3 deploy_refresh/setup_lambda.py
