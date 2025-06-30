import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')

DYNAMODB_TABLE = os.environ['DYNAMODB_TABLE']
table = dynamodb.Table(DYNAMODB_TABLE)

def status(event, context):
    try:
        scan_id = event['pathParameters']['id']
        
        # Get scan result from DynamoDB
        response = table.get_item(Key={'scan_id': scan_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET'
                },
                'body': json.dumps({'error': 'Scan not found'})
            }
        
        item = response['Item']
        
        # Prepare response
        result = {
            'scan_id': item['scan_id'],
            'status': item['status'],
            'created_at': item['created_at'],
            'updated_at': item['updated_at']
        }
        
        if item['status'] == 'COMPLETED':
            result['has_cat'] = item.get('has_cat', False)
            result['answer'] = 'Yes' if item.get('has_cat', False) else 'No'
            result['confidence'] = item.get('cat_confidence', 0)
            
            # Include debug data for power users
            if event.get('queryStringParameters', {}).get('debug') == 'true':
                result['debug_labels'] = item.get('debug_labels', [])
        
        elif item['status'] == 'ERROR':
            result['error_message'] = item.get('error_message', 'Unknown error')
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET'
            },
            'body': json.dumps({'error': str(e)})
        }