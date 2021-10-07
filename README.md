# Workspace Management
This project provides helpers to manage AWS WorkSpaces, providing provisioning, updating, and image/bundle cleanup.

## Workspace Maker
### Provision AWS WorkSpaces based on simple user JSON in GitLab

There are many examples provided by AWS for provisioning workspaces automatically.  Unfortunately, they depend on knowing either detailed attributes about the bundles, or automatically provision based on an AD group.  This function simplifies the process so that simple modification of a JSON file in gitlab causes provisioning of a workspace for that user according to the latest bundle for their team in the requested region.

## Setup
There are some things you need to do to set this up for yourself (see details below):  
 
  - Create, in a gitlab repo accessible from the AWS Lambda function, the simple user JSON that contains the individuals that need an AWS WorkSpace.
  - Customize the configuration JSON teamplate
  - Package and deploy the lambda function to AWS.
  - Generate and store a GitLab Personal Access Token to access the GitLab project's API.
  
### Create simple user JSON accessible from AWS Lambda
This step creates the simple JSON file that contains a dictionary record for each user/workstation/directory/region combination.
* Note: In order to simplify provisioning, this solution requires the alias/Organization Name for your AWS WorkSpace Directory is of the form `(Region)-(Directory)`, e.g., us-west-1-frontend for the `sample_user.json` sample file's first user.
  
* Copy `sample_user.json` to your chosen GitLab Project, and modify, for each user/workstation/directory/region combination:

 - `UserName`: Set to the user's name.
 - `Directory`: Set to the AWS WorkSpace Directory Alias/Organization Name suffix.
 - `Region`: Set to the region, which is also the AWS WorkSpace Directory Alias/Organization Name prefix.
 - `Team`: Set to the user's team, which is also used in the configuration JSON template.

### Customize the configuration JSON template

Edit `config\workspace_config.json` to modify:

* Add the details needed to retrieve the GitLab Token you will store as an AWS secret in the last step of this process in the `secret_info` dictionary:

 - `region`: Set to the AWS Region where you will store the AWS secret containing the token.
 - `name`: Set to the name of the AWS secret key/value pair containing the token.
 - `key`: Set to the key of the AWS secret key/value pair containing the token.

* Modify the `gitlab_url` string to match the web address of your gitlab instance hosting the project containing your user JSON.
* Modify the `gitlab_project_id` string to match the ID of the GitLab project containing your user JSON.
* Modify the `gitlab_filename` string to match the filename of your user JSON.
* Modify the `gitlab_branch` string to match the branch name where your desired user JSON resides.

* For each team that will have workspaces, create a dictionary under `team_workspaces`, modifying:

 - `(Team)` Modify to match the team referenced in the previous section, modifying the following sections:
   - `VolumeEncryptionKey` : Set to the AWS Key Management Service encryption Key ID for this team's WorkSpace Volumes. Note: the IAM Role named ACCOUNT (aws_workspace_maker, by default) must be a user of this key to provision the workspace.
   - `UserVolumeEncryptionEnabled`: Set to `true` to enable encryption the team's WorkSpace User Volumes
   - `RootVolumeEncryptionEnabled`: Set to `true` to enable encryption the team's WorkSpace Root Volumes
   - `Tags` Add a list of tags you want to apply to each of this team's workspaces. Each tag must be a dictionary with the form:
     - `{ "Key": "(tag_key)", "Value": "(tag_value)" } `
   - `WorkspaceProperties` Modify this dictionary's values as appropriate:
     - `RunningMode`: Set to match the desired mode - `AUTO_STOP` or `ALWAYS_ON`
     - `RunningModeAutoStopTimeoutInMinutes`: Set integer to timeout, if `AUTO_STOP`
     - `RootVolumeSizeGib`: Set integer to desired Root Volume size
     - `UserVolumeSizeGib`: Set integer to desired User Volume size
     - `ComputeTypeName`: Set to match the desired compute type - `VALUE`, `STANDARD`, `PERFORMANCE`, `POWER`, or `GRAPHICS`

* Modify the `directory_suffixes` list of strings to match the WorkSpace Directory Alias/Organization Name suffixes that should be provisioned by WorkSpace Maker. These strings provide all possible options for "Directory" in the user JSON.
* Modify the `directory_suffixes_non_encrypted` list of strings to match the WorkSpace Directory Alias/Organization Name suffixes which should not be encrypted; as administration configuration and subsequent image generation requires unencrypted filesystems.
* Modify the `supported_prefix` string to match the prefix used on all your workspace images and bundles.
* Modify the `supported_regions` list of strings to match the regions where the workspace lambda functions should operate.

### Package and deploy the lambda function

1. Edit `vars.sh` to modify the:
   -  desired rate for the lambda function to run inside your VPC.
   -  SUBNET_ID to match a subnet in the region with access to your gitlab instance.
   -  SECURITY_GROUP_ID to match a security group with the appropriate access.
2. Run `./deploy_lambda_function.sh`.  This will:

* Package up the script with its dependencies into the zip format that AWS Lambda expects (as defined in `package.sh`).
* Interact with the AWS API to set up the lambda function with the things it needs (as defined in `deployscripts/setup_lambda.py`):
  * Creates an IAM role for the lambda function to use.  Review the json files in the `deployscripts` directory to see the permissions required.
  * Uploads the zip file from the previous step to create a Lambda function (possibly publishing a new version if the function 
  already exists).

 ### Generate and store a GitLab Personal Access Token 
To make the file accessible to AWS Lambda:

- Generate a GitLab Personal Access Token with "read_api" privileges from a user with access to the given GitLab project.
- Store the token in AWS Secrets Manager as a secret.
- Grant the role (set to `aws_workspace_maker` by `workspacer.py`'s `ACCOUNT` constant) created by the deployment of the AWS Lambda function permissions to read the AWS Secret you just created. Note that if you change the `ACCOUNT` constant, you need to change permissions in `deployscripts\secretsmanager_access.json` by updating the `Resource` path.

## Workspace Refresh

Using the same configuration `config\workspace_config.json` template already created for workspace creation, the workspace refresh AWS Lambda function is designed to execute periodically to run WorkSpace migrations for all workspaces in all managed directories.  The given workspace is migrated to the latest workspace bundle for the given team in the given region.

This refresh function works in conjunction with a image/bundle generation process that should occur before the refresh is scheduled during a given period.

## Workspace Cleanup

Using the same configuration `config\workspace_config.json` template already created for workspace creation, the workspace cleanup AWS Lambda function is designed to execute periodically (after WorkSpace Refresh) to delete old/unused/orphaned Workspace Bundles and Images in all regions. 

This Cleanup function works in conjunction with a image/bundle generation process that must use `supported_prefix` provided in the `config\workspace_config.json` template to prefix all bundles/images used in this workspace maker process. This function should run after the refresh is completed during a given period, to remove all old versions.