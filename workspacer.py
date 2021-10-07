#!/usr/bin/env python
"""
Provisions workspaces based on file
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
import sys

import aws_workspace_utils as aws_ws
import aws_secret_utils as secrets
import gitlab_utils as gitlab
import common_utils as utils


CONFIG_FILE="./config/workspace_config.json"
ACCOUNT = "aws_workspace_maker"


def check_workspace_exists(ws_instance, ws_alias, existing_ws_list, directory_ids):
    '''
    A user can have one workspace in a directory
    '''
    exists = False
    for workspace in existing_ws_list:
        if ws_instance.get('UserName') == workspace.get('UserName') and \
           directory_ids[ws_alias] == workspace.get('DirectoryId'):
            exists = True

    return exists


def determine_new_workspaces(config, bundles, existing_dirs, existing_ws, region, ws_list):
    '''
    Given a set of existing workspaces, determine what needs to be created
    '''
    new_ws = []
    # calculate Aliases, ensure they exist
    aliases_map = get_directory_id_map(region, config.get('directory_suffixes'), existing_dirs)
    aliases = aliases_map.keys()
    #for each requested ws.
    for ws_instance in ws_list:
        if ws_instance['Region'] != region:
            # wrong region
            continue
        # if user exists in directory, don't reprovision.
        ws_alias = '{}-{}'.format(ws_instance.get('Region'), ws_instance.get('Directory'))
        if ws_alias not in aliases:
            print('Error: Requested Directory {} for workspace user {} not found'.format(ws_alias,
                                                                                         ws_instance.get('UserName')))
        elif check_workspace_exists(ws_instance, ws_alias, existing_ws, aliases_map):
            print('Info: Skipping user {} who is already provisioned in {}'.format(ws_instance.get('UserName'),
                                                                                   ws_alias))
        else:
            # Start with team's config from json file
            ws_config = config['team_workspaces'][ws_instance.get('Team')]

            if ws_instance.get('Directory') in config["directory_suffixes_non_encrypted"]:
                # Remove encryption requirements present in config
                del ws_config["VolumeEncryptionKey"]
                del ws_config["UserVolumeEncryptionEnabled"]
                del ws_config["RootVolumeEncryptionEnabled"]
            ws_config['UserName'] = ws_instance['UserName']
            ws_config['DirectoryId'] = aliases_map[ws_alias]
            ws_config['BundleId'] = utils.determine_team_bundle_id(bundles, ws_instance.get('Team'))
            # add to list to provision.
            if ws_config['BundleId']:
                new_ws.append(ws_config)
            else:
                print("Error: Ignoring request to provision workspace for user:{}".format(ws_config.get('UserName')))

    return new_ws


def determine_regions(workstation_list):
    '''
    Return list of regions where requested workspaces should be created
    '''
    regions = []
    if workstation_list:
        regions = {i['Region']: 1 for i in workstation_list}
    return regions


def get_directory_id_map(region, suffixes, existing_dirs):
    '''
    Return the list of directory aliases used by workspace_maker
    '''
    aliases = {}
    existing_aliases = existing_dirs.keys()
    for suffix in suffixes:
        alias = '{}-{}'.format(region, suffix)
        if alias in existing_aliases:
            aliases[alias] = existing_dirs[alias].get('DirectoryId')
        else:
            print("Error: Directory {} not provisioned.".format(alias))

    return aliases


def main(event, context):
    '''
    main function: provision the workspaces
    '''
    # load the config
    config = utils.load_config_json(CONFIG_FILE)

    # load the secret token
    try:
        client = secrets.SecretsClient(config['secret_info'].get('region'))
        secret_name = "{}_{}".format(ACCOUNT, config['secret_info'].get('suffix'))
        token = client.get_aws_secret_value(secret_name,
                                            config['secret_info'].get('key'))
    except TypeError:
        print("Critical: Could not retrieve secret. Are you logged in to AWS?")
        sys.exit(1)

    # load the gitlab file
    client = gitlab.GitLabClient(config.get('gitlab_url'), token)
    if not client.check_gitlab_alive():
        print("Critical: GitLab not healthy.")
        sys.exit(1)
    ws_list = client.get_json_file(config.get('gitlab_project_id'),
                                   config.get('gitlab_filename'),
                                   config.get('gitlab_branch'))
    # Workspaces runs on a region by region basis.
    try:
        regions = determine_regions(ws_list)
    except AttributeError:
        print("No workspaces requested. Exiting normally.")
        sys.exit(0)

    for region in regions:
        client = aws_ws.WorkSpaceClient(region)
        bundles = client.get_current_bundles()
        existing_ws = client.get_current_workspaces()
        existing_dirs = client.get_current_directories()
        new_ws_list = determine_new_workspaces(config, bundles, existing_dirs, existing_ws,
                                               region, ws_list)
        for create_ws in new_ws_list:
            response = client.create_workspace(create_ws)
            if len(response["FailedRequests"]) > 0:
                print("Error: Failed to create workspace for user {}".format(create_ws.get('UserName')))
                for line in response.keys():
                    print("detail:{}: {}".format(line, response[line]))
            else:
                print("Success: Creating workspace for user {}".format(create_ws.get('UserName')))

#main('foo','bar')
