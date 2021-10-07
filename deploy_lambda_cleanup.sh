#!/usr/bin/env bash

. ./vars_cleanup.sh

./package_cleanup.sh

PYTHONPATH=./dist_cleanup:$PYTHONPATH python3 deploy_cleanup/setup_lambda.py
