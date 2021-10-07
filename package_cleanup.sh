#!/usr/bin/env bash
mkdir -p dist_cleanup
rm -rf dist_cleanup/*
rm aws_workspace_cleanup.zip

cp workspacecleanup.py dist_cleanup
cp *_utils.py dist_cleanup
cp -R config dist_cleanup
pip install -r requirements.txt -t dist_cleanup

(cd dist_cleanup && zip -r ../aws_workspace_cleanup *)
