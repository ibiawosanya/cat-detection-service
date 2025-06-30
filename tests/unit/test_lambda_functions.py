### tests/unit/test_lambda_functions.py
```python
import pytest
import json
import boto3
from moto import mock_s3, mock_dynamodb, mock_sqs
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/lambdas'))

@mock_s3
@mock_dynamodb
@mock_sqs
class TestUploadFunction:
    
    def setup_method(self):
        """Setup mock AWS services"""
        # Setup S3
        self.s3 = boto3.client('s3', region_name='eu-west-1')
        self.bucket_name = 'test-bucket'
        self.s3.create_bucket(Bucket=self.bucket_name)
        
        # Setup DynamoDB
        self.dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        self.table_name = 'test-table'
        table = self.dynamodb.create_table(
            TableName=self.table_name,
            KeySchema=[{'AttributeName': 'scan_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'scan_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Setup SQS
        self.sqs = boto3.client('sqs', region_name='eu-west-1')
        queue = self.sqs.create_queue(QueueName='test-queue')
        self.queue_url = queue['QueueUrl']
        
        # Set environment variables
        os.environ['S3_BUCKET'] = self.bucket_name
        os.environ['DYNAMODB_TABLE'] = self.table_name
        os.environ['SQS_QUEUE'] = self.queue_url
    
    def test_upload_valid_image(self):
        """Test uploading valid image"""
        from upload.handler import upload
        
        event = {
            'body': json.dumps({
                'image_data': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==',  # 1x1 PNG
                'content_type': 'image/png',
                'user_id': 'test-user'
            })
        }
        
        result = upload(event, {})
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'scan_id' in body
        assert body['status'] == 'PENDING'
    
    def test_upload_invalid_content_type(self):
        """Test uploading invalid content type"""
        from upload.handler import upload
        
        event = {
            'body': json.dumps({
                'image_data': 'test-data',
                'content_type': 'image/gif',  # Invalid
                'user_id': 'test-user'
            })
        }
        
        result = upload(event, {})
        
        assert result['statusCode'] == 400
        body = json.loads(result['body'])
        assert 'error' in body

@mock_dynamodb
class TestProcessFunction:
    
    def setup_method(self):
        """Setup mock DynamoDB"""
        self.dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        self.table_name = 'test-table'
        table = self.dynamodb.create_table(
            TableName=self.table_name,
            KeySchema=[{'AttributeName': 'scan_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'scan_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        os.environ['DYNAMODB_TABLE'] = self.table_name
    
    @patch('process.handler.rekognition_client')
    def test_process_with_cat(self, mock_rekognition):
        """Test processing image with cat detected"""
        from process.handler import process
        
        # Mock Rekognition response
        mock_rekognition.detect_labels.return_value = {
            'Labels': [
                {'Name': 'Cat', 'Confidence': 95.5},
                {'Name': 'Animal', 'Confidence': 99.0}
            ]
        }
        
        # Create initial record
        table = self.dynamodb.Table(self.table_name)
        scan_id = 'test-scan-id'
        table.put_item(Item={'scan_id': scan_id, 'status': 'PENDING'})
        
        event = {
            'Records': [{
                'body': json.dumps({
                    'scan_id': scan_id,
                    's3_bucket': 'test-bucket',
                    's3_key': 'test-key'
                })
            }]
        }
        
        result = process(event, {})
        
        assert result['statusCode'] == 200
        
        # Check updated record
        response = table.get_item(Key={'scan_id': scan_id})
        item = response['Item']
        assert item['status'] == 'COMPLETED'
        assert item['has_cat'] == True
        assert item['cat_confidence'] == 95.5