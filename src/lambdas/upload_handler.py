import json
import uuid
import os
import boto3
from datetime import datetime, timezone
from typing import Dict, Any

dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle image upload requests with CORS support"""
    
    # CORS headers for all responses
    cors_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token'
    }
    
    try:
        # Handle OPTIONS preflight request
        http_method = event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method', ''))
        
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'message': 'CORS preflight'})
            }
        
        # Handle POST request
        if http_method != 'POST':
            return {
                'statusCode': 405,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Method not allowed'})
            }
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        filename = body.get('filename', '')
        content_type = body.get('contentType', '')
        
        # Validate file type
        if not filename or not content_type:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Missing filename or contentType'})
            }
        
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
        if content_type.lower() not in allowed_types:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Only JPEG and PNG files are allowed'})
            }
        
        # Generate unique scan ID
        scan_id = str(uuid.uuid4())
        
        # Generate S3 key
        file_extension = filename.split('.')[-1].lower()
        s3_key = f"uploads/{scan_id}.{file_extension}"
        
        # Generate presigned URL for upload
        bucket_name = os.environ['IMAGES_BUCKET']
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket_name,
                'Key': s3_key,
                'ContentType': content_type
            },
            ExpiresIn=3600  # 1 hour
        )
        
        # Store initial record in DynamoDB
        table = dynamodb.Table(os.environ['RESULTS_TABLE'])
        timestamp = datetime.now(timezone.utc).isoformat()
        
        table.put_item(
            Item={
                'scanId': scan_id,
                'status': 'PENDING',
                'filename': filename,
                'contentType': content_type,
                's3Key': s3_key,
                'createdAt': timestamp,
                'updatedAt': timestamp
            }
        )
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'scanId': scan_id,
                'uploadUrl': presigned_url,
                'statusUrl': f"/status/{scan_id}"
            })
        }
        
    except Exception as e:
        print(f"Error in upload_handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': 'Internal server error'})
        }