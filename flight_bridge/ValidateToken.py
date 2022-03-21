import json
import os

import cglogging as cgl
import boto3
import jwt
from botocore.exceptions import ClientError

logger_Class = cgl.cglogging()
logger = logger_Class.setup_logging()


class ValidateToken:
    token = ""
    authSupplierId = 0
    authBusinessId = 0
    authUserId = 0
    public_key = os.environ.get('CAG_public_key')
    private_key = os.environ.get('CAG_private_key')
    region = os.environ.get('CAG_REGION')

    @classmethod
    def validate_jwt(cls, token):
        cls.token = token
        logger.debug("inside validate Token")
        try:
            errNum, return_type, errMsg, publicKey = cls.get_public_key(cls.public_key, cls.region)

            decoded = jwt.decode(cls.token, publicKey, algorithms='RS256')

            if 'exp' not in decoded or 'logonType' not in decoded or \
                    'supplierId' not in decoded or 'userId' not in decoded or \
                    'businessId' not in decoded:
                return 8093, 'FATAL', 'Exception, validate token structure'

            else:
                cls.authLogonType = decoded['logonType']
                cls.authSupplierId = decoded['supplierId']
                cls.authBusinessId = decoded['businessId']
                cls.authUserId = decoded['userId']

                return 0, 'GOOD', errMsg

        except Exception as details:
            logger.error('Unexpected error: {0}'.format(details))
            return 8090, 'FATAL', 'Exception, invalid token'

    @classmethod
    def get_public_key(cls, publicSecretName, regionName):
        try:
            logger.debug("insed get public key")
            errNum, errMsg, secret = 0, '', ''

            public_secret_name = publicSecretName
            region_name = regionName

            # Create a Secrets Manager client
            session = boto3.session.Session()
            client = session.client(
                service_name='secretsmanager',
                region_name=region_name
            )

            try:
                get_secret_value_response = client.get_secret_value(
                    SecretId=public_secret_name
                )
            except ClientError as e:
                logger.debug('Unexpected error: {0}'.format(e))
                if e.response['Error']['Code'] == 'DecryptionFailureException':
                    return 8089, 'FATAL', 'DecryptionFailureException', secret
                elif e.response['Error']['Code'] == 'InternalServiceErrorException':
                    return 8089, 'FATAL', 'InternalServiceErrorException', secret
                elif e.response['Error']['Code'] == 'InvalidParameterException':
                    return 8089, 'FATAL', 'InvalidParameterException', secret
                elif e.response['Error']['Code'] == 'InvalidRequestException':
                    return 8089, 'FATAL', 'InvalidRequestException', secret
                elif e.response['Error']['Code'] == 'ResourceNotFoundException':
                    return 8089, 'FATAL', 'ResourceNotFoundException', secret
            else:
                # Decrypts secret using the associated KMS CMK.
                # Depending on whether the secret is a string or binary, one of these fields will be populated.
                if 'SecretString' in get_secret_value_response:
                    secretDict = json.loads(get_secret_value_response['SecretString'])
                    secret = secretDict['PublicKey']

            return errNum, 'GOOD', errMsg, secret
        except Exception as details:
            logger.error('Unexpected error: {0}'.format(details))
        return 8091, 'FATAL', 'Exception, get public key', secret

    @classmethod
    def get_authLogonType(cls):
        return cls.authLogonType

    @classmethod
    def get_authSupplierId(cls):
        return cls.authSupplierId

    @classmethod
    def get_authBusinessId(cls):
        return cls.authBusinessId

    @classmethod
    def get_authUserId(cls):
        return cls.authUserId
