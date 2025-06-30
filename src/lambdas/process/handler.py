import json
import boto3
from datetime import datetime
import os

rekognition_client = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')

DYNAMODB_TABLE = os.environ['DYNAMODB_TABLE']
table = dynamodb.Table(DYNAMODB_TABLE)

def process(event, context):
    for record in event['Records']:
        try:
            # Parse SQS message
            message_body = json.loads(record['body'])
            scan_id = message_body['scan_id']
            s3_bucket = message_body['s3_bucket']
            s3_key = message_body['s3_key']
            
            # Use Rekognition to detect labels
            response = rekognition_client.detect_labels(
                Image={
                    'S3Object': {
                        'Bucket': s3_bucket,
                        'Name': s3_key
                    }
                },
                MaxLabels=50,
                MinConfidence=70
            )
            
            # Check for cat in labels
            has_cat = False
            cat_confidence = 0
            debug_labels = []
            
            for label in response['Labels']:
                debug_labels.append({
                    'name': label['Name'],
                    'confidence': label['Confidence']
                })
                
                if label['Name'].lower() in ['cat', 'kitten', 'feline']:
                    has_cat = True
                    cat_confidence = max(cat_confidence, label['Confidence'])
            
            # Update DynamoDB record
            table.update_item(
                Key={'scan_id': scan_id},
                UpdateExpression='SET #status = :status, has_cat = :has_cat, cat_confidence = :confidence, debug_labels = :labels, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'COMPLETED',
                    ':has_cat': has_cat,
                    ':confidence': cat_confidence,
                    ':labels': debug_labels,
                    ':updated_at': datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            # Update record with error status
            table.update_item(
                Key={'scan_id': scan_id},
                UpdateExpression='SET #status = :status, error_message = :error, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'ERROR',
                    ':error': str(e),
                    ':updated_at': datetime.utcnow().isoformat()
                }
            )
    
    return {'statusCode': 200}