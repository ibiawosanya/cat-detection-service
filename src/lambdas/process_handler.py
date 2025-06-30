import json
import os
import boto3
from datetime import datetime, timezone
from typing import Dict, Any, List
from urllib.parse import unquote

dynamodb = boto3.resource('dynamodb')
rekognition = boto3.client('rekognition')

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Process uploaded images using AWS Rekognition"""
    
    try:
        # Parse S3 event
        for record in event.get('Records', []):
            bucket_name = record['s3']['bucket']['name']
            s3_key = unquote(record['s3']['object']['key'])
            
            # Extract scan ID from S3 key
            if not s3_key.startswith('uploads/'):
                continue
                
            scan_id = s3_key.split('/')[1].split('.')[0]
            
            # Update status to PROCESSING
            table = dynamodb.Table(os.environ['RESULTS_TABLE'])
            timestamp = datetime.now(timezone.utc).isoformat()
            
            table.update_item(
                Key={'scanId': scan_id},
                UpdateExpression='SET #status = :status, updatedAt = :timestamp',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'PROCESSING',
                    ':timestamp': timestamp
                }
            )
            
            try:
                # Call Rekognition to detect labels
                response = rekognition.detect_labels(
                    Image={
                        'S3Object': {
                            'Bucket': bucket_name,
                            'Name': s3_key
                        }
                    },
                    MaxLabels=50,
                    MinConfidence=50.0
                )
                
                # Analyze results for cat detection
                cat_result = analyze_cat_detection(response['Labels'])
                
                # Update DynamoDB with results
                completion_timestamp = datetime.now(timezone.utc).isoformat()
                
                table.update_item(
                    Key={'scanId': scan_id},
                    UpdateExpression='''
                        SET #status = :status,
                            updatedAt = :timestamp,
                            completedAt = :timestamp,
                            containsCat = :containsCat,
                            confidence = :confidence,
                            catLabels = :catLabels,
                            debugData = :debugData
                    ''',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'COMPLETED',
                        ':timestamp': completion_timestamp,
                        ':containsCat': cat_result['contains_cat'],
                        ':confidence': cat_result['confidence'],
                        ':catLabels': cat_result['cat_labels'],
                        ':debugData': {
                            'rekognitionResponse': response,
                            'processingTime': context.get_remaining_time_in_millis(),
                            'imageSize': record['s3']['object'].get('size', 0)
                        }
                    }
                )
                
            except Exception as processing_error:
                print(f"Error processing image {scan_id}: {str(processing_error)}")
                
                # Update status to FAILED
                table.update_item(
                    Key={'scanId': scan_id},
                    UpdateExpression='SET #status = :status, updatedAt = :timestamp, errorMessage = :error',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'FAILED',
                        ':timestamp': datetime.now(timezone.utc).isoformat(),
                        ':error': str(processing_error)
                    }
                )
        
        return {'statusCode': 200}
        
    except Exception as e:
        print(f"Error in process_handler: {str(e)}")
        return {'statusCode': 500}


def analyze_cat_detection(labels: List[Dict]) -> Dict[str, Any]:
    """Analyze Rekognition labels to determine if image contains a cat"""
    
    cat_keywords = ['Cat', 'Kitten', 'Pet', 'Feline']
    cat_labels = []
    max_confidence = 0.0
    
    for label in labels:
        label_name = label['Name']
        confidence = label['Confidence']
        
        # Check for cat-related labels
        if any(keyword.lower() in label_name.lower() for keyword in cat_keywords):
            cat_labels.append({
                'name': label_name,
                'confidence': confidence,
                'instances': label.get('Instances', []),
                'parents': label.get('Parents', [])
            })
            max_confidence = max(max_confidence, confidence)
    
    # Determine if image contains a cat (confidence threshold of 80%)
    contains_cat = max_confidence >= 80.0
    
    return {
        'contains_cat': contains_cat,
        'confidence': round(max_confidence, 2),
        'cat_labels': cat_labels
    }
