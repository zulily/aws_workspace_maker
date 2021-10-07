#!/usr/bin/env bash

. ./vars_maker.sh

./package_maker.sh

PYTHONPATH=./dist_maker:$PYTHONPATH python3 deploy_maker/setup_lambda.py
