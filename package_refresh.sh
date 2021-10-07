#!/usr/bin/env bash
mkdir -p dist_refresh
rm -rf dist_refresh/*
rm aws_workspace_refresh.zip

cp workspacerefresh.py dist_refresh
cp *_utils.py dist_refresh
cp -R config dist_refresh
pip install -r requirements.txt -t dist_refresh

(cd dist_refresh && zip -r ../aws_workspace_refresh *)
