#!/usr/bin/env python
"""
Cleans up down-rev workspace bundles and images that aren't being used
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
ACCOUNT = "aws_workspace_cleanup"


def determine_unattached_images(existing_images, processed_images, zara_prefix):
    '''
    Given a set of images, return the list of non-latest ones unattached to bundles.
    '''
    new_deletes = []
    for image in existing_images.values():
        image_id = image.get('ImageId')
        name = image.get('Name')
        if image_id in processed_images:
            print('Info: Skipping image {} which has been processed already'.format(name))
            continue
        if not name.startswith(zara_prefix):
            print('Info: Skipping image {} not part of workspace_maker'.format(name))
            continue
        print('Info: Queueing unattached image {}'.format(name))
        new_deletes.append(image_id)

    return new_deletes

def get_deletes(ws_list, existing_bundles, existing_images, bundle_map, zara_prefix):
    '''
    Given a set of managed workspaces and bundles, get non-latest bundles and images to delete
    '''
    bundle_deletes = []
    image_deletes = []
    bundled_images = []
    # Determine if each instance has the latest bundle
    used_bundles = [ws.get("BundleId")  for ws in ws_list]
    latest_bundles = bundle_map.values()
    for bundle in existing_bundles.values():
        image_id = bundle.get('ImageId')
        bundled_images.append(image_id)
        bundle_id = bundle.get("BundleId")
        name = bundle.get("Name")
        # if bundle is the latest, skip
        if bundle_id in latest_bundles:
            print('Info: Skipping latest bundle {}'.format(name))
            continue
        # if bundle is attached to workspace (causing delete failure), skip
        if bundle_id in used_bundles:
            print('Info: Skipping bundle {} in use by workspace'.format(name))
            continue
        # if bundle is not part of workspace_maker system, skip
        if not name.startswith(zara_prefix):
            print('Info: Skipping bundle {} not part of workspace_maker'.format(name))
            continue

        print('Info: Queueing bundle/image {}'.format(name))
        bundle_deletes.append(bundle_id)
        image_deletes.append(image_id)

    # add in unbundled images
    image_deletes.extend(determine_unattached_images(existing_images, bundled_images,zara_prefix))

    return bundle_deletes, image_deletes


def get_latest_total_bundle_map(bundles, team_map):
    '''
    Given a set of existing bundles and teams (including default)
    Return latest as a map
    '''
    bundle_map = {}
    teams = list(team_map.keys())
    teams.append("default")
    # calculate Aliases, ensure they exist
    for team in teams:
        bundle_map[team] = utils.determine_team_bundle_id(bundles, team)

    return bundle_map


def main(event, context):
    '''
    main function:cleanup images and bundles
    '''
    # load the config
    config = utils.load_config_json(CONFIG_FILE)

    for region in config['supported_regions']:
        client = aws_ws.WorkSpaceClient(region)
        try:
            print('Examining region {}'.format(region))
            existing_ws = client.get_current_workspaces()
            existing_bundles = client.get_current_bundles()
            existing_images = client.get_current_images()
            bundle_map = get_latest_total_bundle_map(existing_bundles, config['team_workspaces'])
            result = get_deletes(existing_ws, existing_bundles, existing_images, bundle_map,
                                 config['supported_prefix'])
            bundles = result[0]
            images = result[1]
            for bundle in bundles:
                print('Deleting bundleid {} in region {}'.format(bundle, region))
                client.delete_bundle(bundle_id=bundle)
            for image in images:
                print('Deleting imageid {} in region {}'.format(image, region))
                client.delete_image(image_id=image)
        except botocore.exceptions.SSLError:
            print("Info: unable to connect to workspaces in region {}".format(region))


#main('foo','bar')
