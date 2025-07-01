import json
import boto3
import uuid
import base64
from datetime import datetime
import os
from decimal import Decimal

def lambda_handler(event, context):
    """
    Handle image upload requests with original environment variable names.
    """
    
    # Always return CORS headers, even on errors
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    
    try:
        print(f"Upload Lambda started. Event: {json.dumps(event, default=str)}")
        
        # Handle preflight OPTIONS request
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'message': 'CORS preflight'})
            }
        
        # Get environment variables - using your original names
        try:
            s3_bucket = os.environ['S3_BUCKET']
            sqs_queue = os.environ['SQS_QUEUE'] 
            dynamodb_table = os.environ['DYNAMODB_TABLE']
        except KeyError as e:
            error_msg = f"Missing environment variable: {str(e)}"
            print(f"ERROR: {error_msg}")
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({'error': error_msg})
            }
        
        print(f"Environment variables - S3: {s3_bucket}, SQS: {sqs_queue}, DynamoDB: {dynamodb_table}")
        
        # Initialize AWS clients
        try:
            s3_client = boto3.client('s3')
            sqs_client = boto3.client('sqs')
            dynamodb = boto3.resource('dynamodb')
            print("AWS clients initialized successfully")
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({'error': f'Failed to initialize AWS clients: {str(e)}'})
            }
        
        # Parse request body
        if not event.get('body'):
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Request body is required'})
            }
        
        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError as e:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': f'Invalid JSON: {str(e)}'})
            }
        
        print(f"Parsed body keys: {list(body.keys())}")
        
        # Validate required fields
        if 'image_data' not in body:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'image_data field is required'})
            }
        
        if 'content_type' not in body:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'content_type field is required'})
            }
        
        # Validate file type
        content_type = body['content_type']
        if content_type not in ['image/jpeg', 'image/png']:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Only JPEG and PNG files are allowed'})
            }
        
        # Generate unique scan ID
        scan_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        print(f"Generated scan_id: {scan_id}")
        
        # Decode image data
        try:
            image_data = base64.b64decode(body['image_data'])
        except Exception as e:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': f'Invalid base64 image data: {str(e)}'})
            }
        
        print(f"Image decoded, size: {len(image_data)} bytes")
        
        # Upload image to S3
        s3_key = f"images/{scan_id}.{content_type.split('/')[-1]}"
        
        try:
            s3_client.put_object(
                Bucket=s3_bucket,
                Key=s3_key,
                Body=image_data,
                ContentType=content_type
            )
            print(f"Uploaded to S3: s3://{s3_bucket}/{s3_key}")
        except Exception as e:
            print(f"S3 upload error: {str(e)}")
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({'error': f'Failed to upload to S3: {str(e)}'})
            }
        
        # Create initial record in DynamoDB
        try:
            table = dynamodb.Table(dynamodb_table)
            
            # Convert file size to Decimal for DynamoDB
            file_size = Decimal(str(len(image_data)))
            
            table.put_item(
                Item={
                    'scan_id': scan_id,
                    'user_id': body.get('user_id', 'anonymous'),
                    'status': 'PENDING',
                    's3_bucket': s3_bucket,
                    's3_key': s3_key,
                    'image_key': s3_key,  # For compatibility
                    'content_type': content_type,
                    'file_size': file_size,
                    'created_at': timestamp,
                    'updated_at': timestamp
                }
            )
            print(f"Created DynamoDB record for scan_id: {scan_id}")
        except Exception as e:
            print(f"DynamoDB error: {str(e)}")
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({'error': f'Failed to create DynamoDB record: {str(e)}'})
            }
        
        # Send message to SQS for processing
        try:
            sqs_message = {
                'scan_id': scan_id,
                's3_bucket': s3_bucket,
                's3_key': s3_key,
                'image_key': s3_key  # For compatibility
            }
            
            sqs_client.send_message(
                QueueUrl=sqs_queue,
                MessageBody=json.dumps(sqs_message)
            )
            print(f"Sent SQS message for scan_id: {scan_id}")
        except Exception as e:
            print(f"SQS error: {str(e)}")
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({'error': f'Failed to queue for processing: {str(e)}'})
            }
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'scan_id': scan_id,
                'status': 'PENDING',
                'message': 'Image uploaded successfully and queued for processing'
            })
        }
        
    except Exception as e:
        print(f"Unexpected error in upload handler: {str(e)}")
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

# Keep the old function name for compatibility
def upload(event, context):
    return lambda_handler(event, context)