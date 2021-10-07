"""
Helper function for all things workspaces
"""

import boto3

class WorkSpaceClient():
    '''
    A class that abstracts AWS Workspace boto client
    '''
    def __init__(self, region):
        '''
        Create a client to interact with WorkSpaces in a region
        '''
        self.ws_client = boto3.client('workspaces', region_name=region)

    def create_workspace(self, workspace_config):
        '''
        Create a WorkSpace in the given region
        '''
        response = self.ws_client.create_workspaces(Workspaces=[workspace_config])

        return response

    def delete_bundle(self, bundle_id):
        '''
        Delete a Bundle in the given region
        '''
        response = self.ws_client.delete_workspace_bundle(BundleId=bundle_id)

        return response

    def delete_image(self, image_id):
        '''
        Delete an Image in the given region
        '''
        response = self.ws_client.delete_workspace_image(ImageId=image_id)

        return response

    def get_current_bundles(self):
        '''
        Retrieve all bundles in the current region, used for deriving config
        '''
        bundles = None
        response = self.ws_client.describe_workspace_bundles()
        bundles = {i['Name']:i for i in response['Bundles']}

        return bundles

    def get_current_directories(self):
        '''
        Retrieve all directories in the current region, used for deriving config
        '''
        directories = None
        response = self.ws_client.describe_workspace_directories()
        directories = {i['Alias']:i for i in response['Directories']}

        return directories

    def get_current_images(self):
        '''
        Retrieve all images in the current region, used for deriving config
        '''
        images = None
        response = self.ws_client.describe_workspace_images()
        images = {i['Name']:i for i in response['Images']}

        return images

    def get_current_workspaces(self):
        '''
        Retrieve all workspaces in the current region, used for creating the list for creation
        '''
        workspaces = None
        response = self.ws_client.describe_workspaces()
        workspaces = response['Workspaces']

        return workspaces

    def get_tags(self, resource_id):
        '''
        Given a ResourceId, retrieve the tags associated with it, used for determining ownership
        '''
        tags = None
        response = self.ws_client.describe_tags(ResourceId=resource_id)
        tags = response.get('TagList')

        return tags

    def migrate_workspace(self, workspace_id, bundle_id):
        '''
        Migrate a WorkSpace in the given region to the given bundle_id.
        See https://docs.aws.amazon.com/workspaces/latest/adminguide/migrate-workspaces.html
        '''
        response = self.ws_client.migrate_workspace(SourceWorkspaceId=workspace_id,
                                                    BundleId=bundle_id)

        return response
