#!/usr/bin/env bash
mkdir -p dist_maker
rm -rf dist_maker/*
rm aws_workspace_maker.zip

cp workspacer.py dist_maker
cp *_utils.py dist_maker
cp -R config dist_maker
pip install -r requirements.txt -t dist_maker

(cd dist_maker && zip -r ../aws_workspace_maker *)
