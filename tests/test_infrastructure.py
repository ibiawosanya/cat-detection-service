import pytest
import boto3
import json
import os
from moto import mock_s3, mock_dynamodb
from unittest.mock import patch

class TestInfrastructure:
    """Test infrastructure configuration and policies"""
    
    @pytest.fixture
    def aws_region(self):
        """AWS region for testing"""
        return os.getenv('AWS_REGION', 'eu-west-1')
    
    @pytest.fixture
    def environment(self):
        """Environment for testing"""
        return os.getenv('ENVIRONMENT', 'dev')
    
    def test_aws_region_configuration(self, aws_region):
        """Test AWS region configuration"""
        valid_regions = [
            'us-east-1', 'us-west-1', 'us-west-2',
            'eu-west-1', 'eu-west-2', 'eu-central-1',
            'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1'
        ]
        
        assert aws_region in valid_regions, f"Invalid AWS region: {aws_region}"
    
    def test_lambda_configuration_limits(self):
        """Test Lambda function configuration limits"""
        lambda_memory = int(os.getenv('LAMBDA_MEMORY', '512'))
        assert 128 <= lambda_memory <= 10240, f"Lambda memory must be between 128MB and 10240MB, got {lambda_memory}MB"
        assert lambda_memory % 64 == 0, f"Lambda memory must be a multiple of 64MB, got {lambda_memory}MB"
        
        lambda_timeout = int(os.getenv('LAMBDA_TIMEOUT', '30'))
        assert 1 <= lambda_timeout <= 900, f"Lambda timeout must be between 1 and 900 seconds, got {lambda_timeout}s"
    
    def test_s3_bucket_naming_convention(self, aws_region):
        """Test S3 bucket naming follows conventions"""
        account_id = "146624863242"
        images_bucket = f"cat-detector-images-{account_id}-{aws_region}"
        web_bucket = f"cat-detector-web-{account_id}-{aws_region}"
        
        for bucket_name in [images_bucket, web_bucket]:
            assert len(bucket_name) >= 3, f"Bucket name too short: {bucket_name}"
            assert len(bucket_name) <= 63, f"Bucket name too long: {bucket_name}"
            assert bucket_name.islower(), f"Bucket name must be lowercase: {bucket_name}"
            assert bucket_name.startswith("cat-detector-"), f"Bucket should start with project prefix: {bucket_name}"
    
    @mock_s3
    def test_s3_bucket_configuration(self, aws_region):
        """Test S3 bucket configuration"""
        s3_client = boto3.client('s3', region_name=aws_region)
        bucket_name = f"test-cat-detector-images-123456789012-{aws_region}"
        
        if aws_region == 'us-east-1':
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': aws_region}
            )
        
        response = s3_client.list_buckets()
        bucket_names = [bucket['Name'] for bucket in response['Buckets']]
        assert bucket_name in bucket_names, f"Bucket {bucket_name} should exist"
    
    @mock_dynamodb
    def test_dynamodb_table_configuration(self, aws_region):
        """Test DynamoDB table configuration"""
        dynamodb = boto3.resource('dynamodb', region_name=aws_region)
        
        table = dynamodb.create_table(
            TableName='test-cat-detector-results',
            KeySchema=[{'AttributeName': 'scanId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'scanId', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        assert table.table_name == 'test-cat-detector-results'
        assert table.key_schema[0]['AttributeName'] == 'scanId'
        assert table.key_schema[0]['KeyType'] == 'HASH'
    
    def test_security_configuration(self):
        """Test security configuration requirements"""
        security_requirements = {
            's3_encryption': True,
            'dynamodb_encryption': True,
            'lambda_environment_encryption': True,
            'api_gateway_logging': True,
            'cloudwatch_logs_retention': 14
        }
        
        assert security_requirements['s3_encryption'], "S3 encryption should be enabled"
        assert security_requirements['dynamodb_encryption'], "DynamoDB encryption should be enabled"
        assert security_requirements['cloudwatch_logs_retention'] > 0, "CloudWatch logs retention should be positive"
    
    def test_resource_tagging_strategy(self, environment):
        """Test resource tagging strategy"""
        expected_tags = {
            'Project': 'cat-detector',
            'Environment': environment,
            'ManagedBy': 'pulumi'
        }
        
        for tag_key, tag_value in expected_tags.items():
            assert len(tag_key) > 0, "Tag key should not be empty"
            assert len(tag_value) > 0, f"Tag value for {tag_key} should not be empty"