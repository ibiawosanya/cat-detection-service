import json
import boto3
import uuid
import os
from datetime import datetime
from decimal import Decimal

# Initialize AWS clients
s3 = boto3.client('s3')
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')

# Environment variables
IMAGES_BUCKET = os.environ['IMAGES_BUCKET']
PROCESSING_QUEUE_URL = os.environ['PROCESSING_QUEUE_URL']
RESULTS_TABLE = os.environ['RESULTS_TABLE']

def lambda_handler(event, context):
    """
    Handle image upload requests.
    Validates file type, stores in S3, creates DynamoDB record, and queues for processing.
    """
    
    try:
        # Enable CORS for all responses
        cors_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        }
        
        # Handle preflight OPTIONS request
        if event['httpMethod'] == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'message': 'CORS preflight'})
            }
        
        # Parse the request body
        if event.get('isBase64Encoded', False):
            import base64
            body = base64.b64decode(event['body'])
            content_type = event['headers'].get('content-type', event['headers'].get('Content-Type', ''))
        else:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Request body must be base64 encoded'})
            }
        
        # Validate content type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
        if content_type not in allowed_types:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': f'Invalid file type. Only JPEG and PNG files are allowed. Received: {content_type}'
                })
            }
        
        # Generate unique identifiers
        scan_id = str(uuid.uuid4())
        file_extension = 'jpg' if content_type in ['image/jpeg', 'image/jpg'] else 'png'
        image_key = f"uploads/{scan_id}.{file_extension}"
        
        # Upload image to S3
        s3.put_object(
            Bucket=IMAGES_BUCKET,
            Key=image_key,
            Body=body,
            ContentType=content_type
        )
        
        # Create initial record in DynamoDB (with Decimal types)
        table = dynamodb.Table(RESULTS_TABLE)
        
        # Convert any numeric values to Decimal for DynamoDB
        timestamp = datetime.utcnow().isoformat()
        file_size_decimal = Decimal(str(len(body)))  # Convert file size to Decimal
        
        initial_record = {
            'scan_id': scan_id,
            'image_key': image_key,
            'status': 'QUEUED',
            'file_size': file_size_decimal,
            'content_type': content_type,
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        table.put_item(Item=initial_record)
        
        # Send message to SQS for processing
        message_body = {
            'scan_id': scan_id,
            'image_key': image_key,
            'content_type': content_type
        }
        
        sqs.send_message(
            QueueUrl=PROCESSING_QUEUE_URL,
            MessageBody=json.dumps(message_body)
        )
        
        print(f"Successfully uploaded image {image_key} with scan ID {scan_id}")
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'scan_id': scan_id,
                'message': 'Image uploaded successfully and queued for processing',
                'image_key': image_key
            })
        }
        
    except Exception as e:
        print(f"Error in upload handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e)
            })
        }