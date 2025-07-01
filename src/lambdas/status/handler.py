import json
import boto3
import os
from decimal import Decimal

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables - using original name
DYNAMODB_TABLE = os.environ['DYNAMODB_TABLE']

def lambda_handler(event, context):
    """
    Retrieve scan status and results from DynamoDB.
    """
    
    try:
        # Enable CORS for all responses
        cors_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,GET'
        }
        
        # Handle preflight OPTIONS request
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'message': 'CORS preflight'})
            }
        
        # Extract scan_id from path parameters - your API uses 'id'
        path_params = event.get('pathParameters') or {}
        scan_id = path_params.get('id')  # Your API Gateway uses {id} not {scan_id}
        
        if not scan_id:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'scan_id is required'})
            }
        
        print(f"Looking up scan_id: {scan_id}")
        
        # Check for debug mode
        query_params = event.get('queryStringParameters') or {}
        debug_mode = query_params.get('debug', 'false').lower() == 'true'
        
        # Get item from DynamoDB
        table = dynamodb.Table(DYNAMODB_TABLE)
        
        response = table.get_item(
            Key={'scan_id': scan_id}
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Scan not found'})
            }
        
        item = response['Item']
        print(f"Found item with status: {item.get('status')}")
        
        # Convert Decimal types back to float/int for JSON serialization
        def decimal_to_number(obj):
            """Convert DynamoDB Decimal types to regular numbers for JSON"""
            if isinstance(obj, dict):
                return {k: decimal_to_number(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [decimal_to_number(v) for v in obj]
            elif isinstance(obj, Decimal):
                # Convert Decimal to int if it's a whole number, otherwise float
                if obj % 1 == 0:
                    return int(obj)
                else:
                    return float(obj)
            else:
                return obj
        
        # Convert all Decimal types in the item
        item = decimal_to_number(item)
        
        # Prepare the response based on status
        result = {
            'scan_id': item['scan_id'],
            'status': item['status'],
            'created_at': item.get('created_at'),
            'updated_at': item.get('updated_at')
        }
        
        # Add error message if present
        if 'error_message' in item:
            result['error_message'] = item['error_message']
        
        # Add results if completed - handle both old and new field names
        if item['status'] == 'COMPLETED':
            # Try new field names first, fall back to old ones
            cats_found = item.get('cats_found', item.get('has_cat', False))
            cat_count = item.get('cat_count', 1 if cats_found else 0)
            highest_confidence = item.get('highest_confidence', item.get('cat_confidence', 0))
            
            result.update({
                'cats_found': cats_found,
                'cat_count': cat_count,
                'highest_confidence': highest_confidence,
                'total_labels': item.get('total_labels', 0),
                # Legacy fields for compatibility
                'has_cat': cats_found,
                'answer': 'Yes' if cats_found else 'No',
                'confidence': highest_confidence
            })
            
            # Add debug data if requested
            if debug_mode:
                if 'debug_data' in item:
                    result['debug_data'] = item['debug_data']
                elif 'debug_labels' in item:
                    result['debug_labels'] = item['debug_labels']
        
        print(f"Returning result: {json.dumps(result, indent=2)}")
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        print(f"Error in status handler: {str(e)}")
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
def status(event, context):
    return lambda_handler(event, context)