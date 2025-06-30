import json
import boto3
import os
from decimal import Decimal
from datetime import datetime

# Initialize AWS clients
rekognition = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')

# Environment variables
RESULTS_TABLE = os.environ['RESULTS_TABLE']
IMAGES_BUCKET = os.environ['IMAGES_BUCKET']

def lambda_handler(event, context):
    """
    Process SQS messages containing image scan requests.
    Uses AWS Rekognition to detect cats and stores results in DynamoDB.
    """
    
    try:
        # Process each SQS record
        for record in event['Records']:
            message_body = json.loads(record['body'])
            scan_id = message_body['scan_id']
            image_key = message_body['image_key']
            
            print(f"Processing scan {scan_id} for image {image_key}")
            
            # Update status to processing
            update_scan_status(scan_id, 'PROCESSING')
            
            try:
                # Perform cat detection
                result = detect_cats_in_image(image_key)
                
                # Store results
                store_scan_results(scan_id, image_key, result)
                
                print(f"Successfully processed scan {scan_id}")
                
            except Exception as e:
                print(f"Error processing scan {scan_id}: {str(e)}")
                # Update status to error
                update_scan_status(scan_id, 'ERROR', str(e))
                raise
    
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        raise

def detect_cats_in_image(image_key):
    """
    Use AWS Rekognition to detect cats in the image.
    """
    try:
        # Call Rekognition to detect labels
        response = rekognition.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': IMAGES_BUCKET,
                    'Name': image_key
                }
            },
            MaxLabels=20,
            MinConfidence=70.0
        )
        
        # Process the response to find cat-related labels
        cat_labels = []
        all_labels = []
        
        for label in response['Labels']:
            # Convert floats to Decimals for DynamoDB
            label_data = {
                'Name': label['Name'],
                'Confidence': Decimal(str(round(label['Confidence'], 2))),
                'Categories': [cat['Name'] for cat in label.get('Categories', [])],
                'Instances': []
            }
            
            # Process instances (bounding boxes) if present
            for instance in label.get('Instances', []):
                instance_data = {
                    'Confidence': Decimal(str(round(instance['Confidence'], 2)))
                }
                
                # Add bounding box if present
                if 'BoundingBox' in instance:
                    bbox = instance['BoundingBox']
                    instance_data['BoundingBox'] = {
                        'Width': Decimal(str(round(bbox['Width'], 4))),
                        'Height': Decimal(str(round(bbox['Height'], 4))),
                        'Left': Decimal(str(round(bbox['Left'], 4))),
                        'Top': Decimal(str(round(bbox['Top'], 4)))
                    }
                
                label_data['Instances'].append(instance_data)
            
            all_labels.append(label_data)
            
            # Check if this is a cat-related label
            if is_cat_related(label['Name']):
                cat_labels.append(label_data)
        
        # Determine if cats were found
        cats_found = len(cat_labels) > 0
        
        # Calculate highest confidence cat detection
        highest_confidence = Decimal('0')
        if cat_labels:
            highest_confidence = max(label['Confidence'] for label in cat_labels)
        
        return {
            'cats_found': cats_found,
            'cat_count': len(cat_labels),
            'highest_confidence': highest_confidence,
            'cat_labels': cat_labels,
            'all_labels': all_labels,
            'total_labels': len(all_labels)
        }
        
    except Exception as e:
        print(f"Error in detect_cats_in_image: {str(e)}")
        raise

def is_cat_related(label_name):
    """
    Check if a label is cat-related.
    """
    cat_keywords = [
        'cat', 'kitten', 'feline', 'tabby', 'siamese', 
        'persian', 'maine coon', 'ragdoll', 'british shorthair'
    ]
    
    label_lower = label_name.lower()
    return any(keyword in label_lower for keyword in cat_keywords)

def update_scan_status(scan_id, status, error_message=None):
    """
    Update the scan status in DynamoDB.
    """
    try:
        table = dynamodb.Table(RESULTS_TABLE)
        
        update_expression = "SET #status = :status, #updated = :updated"
        expression_attribute_names = {
            '#status': 'status',
            '#updated': 'updated_at'
        }
        expression_attribute_values = {
            ':status': status,
            ':updated': datetime.utcnow().isoformat()
        }
        
        if error_message:
            update_expression += ", #error = :error"
            expression_attribute_names['#error'] = 'error_message'
            expression_attribute_values[':error'] = error_message
        
        table.update_item(
            Key={'scan_id': scan_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values
        )
        
    except Exception as e:
        print(f"Error updating scan status: {str(e)}")
        raise

def store_scan_results(scan_id, image_key, detection_result):
    """
    Store the complete scan results in DynamoDB.
    """
    try:
        table = dynamodb.Table(RESULTS_TABLE)
        
        # Prepare the item for DynamoDB
        item = {
            'scan_id': scan_id,
            'image_key': image_key,
            'status': 'COMPLETED',
            'cats_found': detection_result['cats_found'],
            'cat_count': detection_result['cat_count'],
            'highest_confidence': detection_result['highest_confidence'],
            'total_labels': detection_result['total_labels'],
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Add detailed results for debug mode
        item['debug_data'] = {
            'cat_labels': detection_result['cat_labels'],
            'all_labels': detection_result['all_labels']
        }
        
        # Store in DynamoDB
        table.put_item(Item=item)
        
        print(f"Stored results for scan {scan_id}")
        
    except Exception as e:
        print(f"Error storing scan results: {str(e)}")
        raise