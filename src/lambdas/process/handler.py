import json
import boto3
import os
from decimal import Decimal
from datetime import datetime

def process(event, context):
    """
    Process SQS messages containing image scan requests.
    Uses AWS Rekognition to detect cats and stores results in DynamoDB.
    """
    
    try:
        print(f"Process Lambda started. Available env vars: {list(os.environ.keys())}")
        
        # Initialize AWS clients
        rekognition = boto3.client('rekognition')
        dynamodb = boto3.resource('dynamodb')
        
        # Get environment variables
        dynamodb_table = os.environ['DYNAMODB_TABLE']
        print(f"Using DynamoDB table: {dynamodb_table}")
        
        # Process each SQS record
        for record in event['Records']:
            message_body = json.loads(record['body'])
            scan_id = message_body['scan_id']
            
            # Get S3 info from the message (not environment variables)
            s3_bucket = message_body.get('s3_bucket')
            image_key = message_body.get('image_key') or message_body.get('s3_key')
            
            print(f"Processing scan {scan_id} for image {image_key} in bucket {s3_bucket}")
            
            if not s3_bucket or not image_key:
                raise Exception(f"Missing S3 info in message: bucket={s3_bucket}, key={image_key}")
            
            # Update status to processing
            update_scan_status(scan_id, 'PROCESSING', dynamodb_table)
            
            try:
                # Perform cat detection
                result = detect_cats_in_image(image_key, s3_bucket)
                
                # Store results
                store_scan_results(scan_id, image_key, result, dynamodb_table)
                
                print(f"Successfully processed scan {scan_id}")
                
            except Exception as e:
                print(f"Error processing scan {scan_id}: {str(e)}")
                # Update status to error
                update_scan_status(scan_id, 'ERROR', dynamodb_table, str(e))
                raise
    
    except Exception as e:
        print(f"Error in process handler: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise

def detect_cats_in_image(image_key, bucket_name):
    """
    Use AWS Rekognition to detect cats in the image.
    """
    try:
        rekognition = boto3.client('rekognition')
        
        print(f"Calling Rekognition for s3://{bucket_name}/{image_key}")
        
        # Call Rekognition to detect labels
        response = rekognition.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': image_key
                }
            },
            MaxLabels=20,
            MinConfidence=70.0
        )
        
        print(f"Rekognition found {len(response['Labels'])} labels")
        
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
                print(f"Found cat label: {label['Name']} with confidence {label['Confidence']}")
        
        # Determine if cats were found
        cats_found = len(cat_labels) > 0
        
        # Calculate highest confidence cat detection
        highest_confidence = Decimal('0')
        if cat_labels:
            highest_confidence = max(label['Confidence'] for label in cat_labels)
        
        print(f"Cat detection result: cats_found={cats_found}, count={len(cat_labels)}, highest_confidence={highest_confidence}")
        
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
        import traceback
        print(traceback.format_exc())
        raise

def is_cat_related(label_name):
    """
    Check if a label is cat-related with improved logic.
    """
    cat_keywords = [
        'cat', 'kitten', 'feline', 'tabby', 'siamese', 
        'persian', 'maine coon', 'ragdoll', 'british shorthair'
    ]
    
    # Words that contain "cat" but are NOT cats
    non_cat_words = [
        'cattle', 'catch', 'category', 'catalog', 'caterpillar', 
        'scatter', 'locate', 'education', 'vacation', 'delicate'
    ]
    
    label_lower = label_name.lower()
    
    # If it's explicitly not a cat, return False
    if any(non_cat in label_lower for non_cat in non_cat_words):
        return False
    
    # Check for cat keywords
    return any(keyword in label_lower for keyword in cat_keywords)

def update_scan_status(scan_id, status, table_name, error_message=None):
    """
    Update the scan status in DynamoDB.
    """
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        
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
        
        print(f"Updated scan {scan_id} status to {status}")
        
    except Exception as e:
        print(f"Error updating scan status: {str(e)}")
        raise

def store_scan_results(scan_id, image_key, detection_result, table_name):
    """
    Store the complete scan results in DynamoDB.
    """
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        
        # Prepare the item for DynamoDB with both old and new field names for compatibility
        timestamp = datetime.utcnow().isoformat()
        cats_found = detection_result['cats_found']
        highest_confidence = detection_result['highest_confidence']
        
        item = {
            'scan_id': scan_id,
            'image_key': image_key,
            's3_key': image_key,  # For compatibility
            'status': 'COMPLETED',
            
            # New field names
            'cats_found': cats_found,
            'cat_count': detection_result['cat_count'],
            'highest_confidence': highest_confidence,
            'total_labels': detection_result['total_labels'],
            
            # Legacy field names for compatibility
            'has_cat': cats_found,
            'cat_confidence': highest_confidence,
            
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        # Add detailed results for debug mode
        item['debug_data'] = {
            'cat_labels': detection_result['cat_labels'],
            'all_labels': detection_result['all_labels']
        }
        
        # Legacy debug data field
        item['debug_labels'] = detection_result['all_labels']
        
        # Store in DynamoDB
        table.put_item(Item=item)
        
        print(f"Stored results for scan {scan_id}: cats_found={cats_found}, confidence={highest_confidence}")
        
    except Exception as e:
        print(f"Error storing scan results: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise