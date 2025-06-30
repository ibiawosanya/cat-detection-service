import json
import boto3
import uuid
import base64
from datetime import datetime
import os

s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')

S3_BUCKET = os.environ['S3_BUCKET']
SQS_QUEUE = os.environ['SQS_QUEUE']
DYNAMODB_TABLE = os.environ['DYNAMODB_TABLE']

table = dynamodb.Table(DYNAMODB_TABLE)

def upload(event, context):
    try:
        # Parse request
        body = json.loads(event['body'])
        
        # Validate file type
        content_type = body.get('content_type', '')
        if content_type not in ['image/jpeg', 'image/png']:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST'
                },
                'body': json.dumps({'error': 'Only JPEG and PNG files are allowed'})
            }
        
        # Generate unique scan ID
        scan_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Decode and upload image to S3
        image_data = base64.b64decode(body['image_data'])
        s3_key = f"images/{scan_id}.{content_type.split('/')[-1]}"
        
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=image_data,
            ContentType=content_type
        )
        
        # Create initial record in DynamoDB
        table.put_item(
            Item={
                'scan_id': scan_id,
                'user_id': body.get('user_id', 'anonymous'),
                'status': 'PENDING',
                's3_bucket': S3_BUCKET,
                's3_key': s3_key,
                'content_type': content_type,
                'created_at': timestamp,
                'updated_at': timestamp
            }
        )
        
        # Send message to SQS for processing
        sqs_client.send_message(
            QueueUrl=SQS_QUEUE,
            MessageBody=json.dumps({
                'scan_id': scan_id,
                's3_bucket': S3_BUCKET,
                's3_key': s3_key
            })
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST'
            },
            'body': json.dumps({
                'scan_id': scan_id,
                'status': 'PENDING',
                'message': 'Image uploaded successfully and queued for processing'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST'
            },
            'body': json.dumps({'error': str(e)})
        }