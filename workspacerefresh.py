#!/usr/bin/env python
"""
Refreshes workspaces if later build is available
Called via lambda function

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

import botocore

import aws_workspace_utils as aws_ws
import common_utils as utils

CONFIG_FILE="./config/workspace_config.json"
ACCOUNT = "aws_workspace_refresh"


def get_ws_updates(client, ws_list, bundle_map):
    '''
    Given a set of managed workspaces, determine update targets
    '''
    ws_updates = []
    # Determine if each instance has the latest bundle
    for ws_inst in ws_list:
        user = ws_inst.get('UserName')
        tags = client.get_tags(ws_inst.get('WorkspaceId'))
        tag_dict = {tag['Key']: tag['Value'] for tag in tags}
        team = tag_dict.get('team')
        try:
            if ws_inst.get('BundleId') == bundle_map[team]:
                print('Info: Skipping user {} who has latest {} bundle'.format(user,
                                                                               team))
            else:
                # Add workstation to update list as dict
                ws_info = {'UserName': user,
                           'Team': team,
                           'WorkSpaceId': ws_inst.get('WorkspaceId'),
                           'BundleId': bundle_map[team]}
                ws_updates.append(ws_info)
        except KeyError:
            print('WARNING: Could not find bundle for team {}'.format(team))
            print('WARNING: Skipping update: user {}, workstation {}'.format(user,
             ws_inst.get('WorkspaceId')))

    return ws_updates


def get_directory_ids(region, suffixes, existing_dirs):
    '''
    Return the list of directory ids managed by workspace_maker in a region
    '''
    ids = []
    existing_aliases = existing_dirs.keys()
    for suffix in suffixes:
        alias = '{}-{}'.format(region, suffix)
        if alias in existing_aliases:
            ids.append(existing_dirs[alias].get('DirectoryId'))

    return ids

def get_latest_bundle_map(bundles, teams):
    '''
    Given a set of bundles, determine which is latest for team
    '''
    bundle_map = {}
    # calculate Aliases, ensure they exist
    for team in teams:
        bundle_map[team] = utils.determine_team_bundle_id(bundles, team)

    return bundle_map

def get_managed_workspaces(existing_ws_list, directory_ids):
    '''
    A workspace must be in a managed directory
    '''
    managed_ws = []
    for workspace in existing_ws_list:
        if workspace.get('DirectoryId') in directory_ids:
            managed_ws.append(workspace)

    return managed_ws


def main(event, context):
    '''
    main function: refresh OS drive using latest images
    '''
    # load the config
    config = utils.load_config_json(CONFIG_FILE)

    for region in config['supported_regions']:
        client = aws_ws.WorkSpaceClient(region)
        try:
            print('Examining region {}'.format(region))
            existing_dirs = client.get_current_directories()
            managed_ids = get_directory_ids(region, config['directory_suffixes'], existing_dirs)
            existing_ws = client.get_current_workspaces()
            managed_ws = get_managed_workspaces(existing_ws, managed_ids)
            existing_bundles = client.get_current_bundles()
            bundle_map = get_latest_bundle_map(existing_bundles, config['team_workspaces'].keys())
            ws_refresh = get_ws_updates(client, managed_ws, bundle_map)
            for workspace in ws_refresh:
                print('Migrating user {} in region {}'.format(workspace.get('UserName'), region))
                client.migrate_workspace(workspace_id=workspace.get('WorkSpaceId'),
                                         bundle_id=workspace.get('BundleId'))
        except botocore.exceptions.SSLError:
            print("Info: unable to connect to workspaces in region {}".format(region))


#main('foo','bar')
