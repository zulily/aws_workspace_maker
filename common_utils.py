#!/usr/bin/env python
"""
   Helper file with common utilities

   Copyright 2021 Zulily, Inc.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import json
import re


def determine_team_bundle_id(bundles, team):
    '''
    Get latest bundle for the given team
    '''
    latest_default = 0
    latest_patch = 0
    default_name = None
    patch_name = None
    latest_bundle_id = None
    names = bundles.keys()
    for name in names:
        # get team bundles
        match = re.match(r"^.*?_(\d+)_?(\w*)?$", name)
        patch_date = match.group(1)
        bundle_team = match.group(2)
        if not bundle_team and int(patch_date) > latest_default:
            latest_default = int(patch_date)
            default_name = name
        elif bundle_team == team and int(patch_date) > latest_patch:
            latest_patch = int(patch_date)
            patch_name = name
    if patch_name:
        latest_bundle_id = bundles[patch_name].get('BundleId')
    elif default_name:
        latest_bundle_id = bundles[default_name].get('BundleId')
    else:
        print("Error: No patch found for team {}".format(team))

    return latest_bundle_id


def load_config_json(file_name):
    '''
    Load JSON configuration
    '''
    mydict = None
    try:
        with open(file_name, 'r') as deffile:
            mydict = json.load(deffile)
    except ValueError as error:
        print('Failed to load file: %s', file_name)
        print('Critical: %s', str(error))
    return mydict
