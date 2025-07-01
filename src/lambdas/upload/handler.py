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

# Environment variables - MUST match your Terraform configuration
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
        
        print(f"Received upload request: {event['httpMethod']}")
        
        # Parse the request body - handle both base64 and direct upload
        if event.get('isBase64Encoded', False):
            import base64
            body = base64.b64decode(event['body'])
            content_type = event['headers'].get('content-type', event['headers'].get('Content-Type', ''))
        else:
            # Try to parse JSON body (for testing)
            try:
                json_body = json.loads(event['body'])
                if 'image_data' in json_body:
                    # Base64 encoded image in JSON
                    import base64
                    body = base64.b64decode(json_body['image_data'])
                    content_type = json_body.get('content_type', 'image/jpeg')
                else:
                    return {
                        'statusCode': 400,
                        'headers': cors_headers,
                        'body': json.dumps({'error': 'image_data field required in JSON body'})
                    }
            except:
                return {
                    'statusCode': 400,
                    'headers': cors_headers,
                    'body': json.dumps({'error': 'Invalid request format'})
                }
        
        print(f"Content type: {content_type}, Body size: {len(body)}")
        
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
        
        print(f"Generated scan_id: {scan_id}, image_key: {image_key}")
        
        # Upload image to S3
        s3.put_object(
            Bucket=IMAGES_BUCKET,
            Key=image_key,
            Body=body,
            ContentType=content_type
        )
        print(f"Uploaded to S3: s3://{IMAGES_BUCKET}/{image_key}")
        
        # Create initial record in DynamoDB (with Decimal types)
        table = dynamodb.Table(RESULTS_TABLE)
        
        timestamp = datetime.utcnow().isoformat()
        file_size_decimal = Decimal(str(len(body)))  # Convert file size to Decimal
        
        initial_record = {
            'scan_id': scan_id,
            'image_key': image_key,
            'status': 'PENDING',  # Changed from QUEUED to PENDING for consistency
            'file_size': file_size_decimal,
            'content_type': content_type,
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        table.put_item(Item=initial_record)
        print(f"Created DynamoDB record for scan_id: {scan_id}")
        
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
        print(f"Sent SQS message for scan_id: {scan_id}")
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'scan_id': scan_id,
                'message': 'Image uploaded successfully and queued for processing',
                'image_key': image_key,
                'status': 'PENDING'
            })
        }
        
    except Exception as e:
        print(f"Error in upload handler: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e)
            })
        }