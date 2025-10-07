import os

class AWSCredentials:

    def __init__(self):
        self.aws_profile = os.getenv('AWS_PROFILE', 'default')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')