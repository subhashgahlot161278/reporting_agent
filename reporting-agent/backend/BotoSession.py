class BotoSession:
    def __init__(self, awsCredntials: AWSCredentials):
        self.awsCredntials = awsCredntials
        self.session = self.__getSession

    def __getSession(): 
        if awsCredntials.aws_access_key and awsCredntials.aws_secret_key:
        try:
            session = boto3.Session(
                aws_access_key_id=wsCredntials.aws_access_key,
                aws_secret_access_key=awsCredntials.aws_secret_key,
                region_name=awsCredntials.aws_region
            )
            # Test the credentials
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            print(f"✅ Using AWS access keys")
            print(f"   Account: {identity.get('Account', 'Unknown')}")
            print(f"   Access Key: {aws_access_key[:8]}...")
            print(f"   Region: {aws_region}")
            print("⚠️  Note: Using access keys - ensure AgentCore permissions are attached to this user")
            return session, aws_region
            
        except Exception as e:
            print(f"❌ Access key authentication failed: {e}")
            raise Exception(f"AWS authentication failed: {e}")
        else:
            print("❌ No AWS access keys found in environment variables")
            raise Exception("No AWS credentials available. Please configure AWS profile or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")    

    def getSession():
        return self.session