"""
Helper function to retrieve AWS Secrets
"""
import base64
import json
import boto3
from botocore.exceptions import ClientError

class SecretsClient():
    '''
    Class to interact with AWS Secrets Manager
    '''
    def __init__(self, region):
        self.secrets_client = boto3.client(service_name='secretsmanager',
                                           region_name=region)


    def get_aws_secret(self, secret_name):
        '''
        Wraps process of retrieve and decoding secret
        '''
        secret = None
        try:
            secret_value = self.secrets_client.get_secret_value(
                SecretId=secret_name
            )
        except ClientError as err:
            if err.response['Error']['Code'] in {
                'DecryptionFailureException',
                'InternalServiceErrorException',
                'InvalidParameterException',
                'InvalidRequestException',
                'ResourceNotFoundException'}:
                raise err
        else:
            # Decrypts secret using the associated KMS CMK.
            # Whether secret is a string or binary, one of the fields are populated
            if 'SecretString' in secret_value:
                secret = secret_value['SecretString']
            else:
                secret = base64.b64decode(secret_value['SecretBinary'])
        return secret

    def get_aws_secret_value(self, secret_name, key):
        '''
        will retrieve secret, then return the value pointed at by given key
        '''
        secret_map = self.get_aws_secret(secret_name)
        secret = json.loads(secret_map)
        return secret.get(key)
