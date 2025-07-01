import json
import boto3
import os
from decimal import Decimal

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables - MUST match your Terraform configuration
RESULTS_TABLE = os.environ['RESULTS_TABLE']

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
        if event['httpMethod'] == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'message': 'CORS preflight'})
            }
        
        # Extract scan_id from path parameters
        # Handle both 'scan_id' and 'id' for compatibility
        path_params = event.get('pathParameters') or {}
        scan_id = path_params.get('scan_id') or path_params.get('id')
        
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
        table = dynamodb.Table(RESULTS_TABLE)
        
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
        
        # Prepare the response based on status and debug mode
        result = {
            'scan_id': item['scan_id'],
            'status': item['status'],
            'created_at': item.get('created_at'),
            'updated_at': item.get('updated_at')
        }
        
        # Add error message if present
        if 'error_message' in item:
            result['error_message'] = item['error_message']
        
        # Add results if completed
        if item['status'] == 'COMPLETED':
            # Use the field names that match the process lambda output
            result.update({
                'cats_found': item.get('cats_found', False),
                'cat_count': item.get('cat_count', 0),
                'highest_confidence': item.get('highest_confidence', 0),
                'total_labels': item.get('total_labels', 0)
            })
            
            # Add debug data if requested
            if debug_mode and 'debug_data' in item:
                result['debug_data'] = item['debug_data']
        
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