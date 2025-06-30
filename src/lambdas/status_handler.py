import json
import os
import boto3
from typing import Dict, Any
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle status and debug requests"""
    
    try:
        # Extract scan ID from path parameters
        scan_id = event.get('pathParameters', {}).get('scanId')
        if not scan_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing scanId parameter'})
            }
        
        # Check if this is a debug request
        path = event.get('path', '')
        is_debug_request = '/debug/' in path
        
        # Query DynamoDB for scan results
        table = dynamodb.Table(os.environ['RESULTS_TABLE'])
        response = table.get_item(Key={'scanId': scan_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Scan not found'})
            }
        
        item = response['Item']
        
        # Build response based on request type
        if is_debug_request:
            # Return debug information for power users
            debug_response = {
                'scanId': scan_id,
                'status': item['status'],
                'filename': item.get('filename'),
                'contentType': item.get('contentType'),
                'createdAt': item.get('createdAt'),
                'updatedAt': item.get('updatedAt'),
                'debugData': item.get('debugData', {}),
                'catLabels': item.get('catLabels', []),
                'errorMessage': item.get('errorMessage')
            }
            
            if item['status'] == 'COMPLETED':
                debug_response.update({
                    'containsCat': item.get('containsCat'),
                    'confidence': item.get('confidence'),
                    'completedAt': item.get('completedAt')
                })
            
            response_body = debug_response
        else:
            # Return standard status response
            status_response = {
                'scanId': scan_id,
                'status': item['status'],
                'timestamp': item.get('updatedAt')
            }
            
            if item['status'] == 'COMPLETED':
                status_response['result'] = {
                    'containsCat': item.get('containsCat'),
                    'confidence': item.get('confidence')
                }
            elif item['status'] == 'FAILED':
                status_response['error'] = item.get('errorMessage', 'Unknown error')
            
            response_body = status_response
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_body, default=str)
        }
        
    except Exception as e:
        print(f"Error in status_handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }
