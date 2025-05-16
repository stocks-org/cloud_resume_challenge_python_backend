import json
import boto3
import os
from botocore.exceptions import ClientError
from decimal import Decimal

# Get table name from environment variable (set by CDK)
TABLE_NAME = os.environ.get('TABLE_NAME', 'PageHitCounters')

# Initialize the DynamoDB resource
dynamodb = boto3.resource('dynamodb')
# Reference the counters table using the environment variable
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    try:
        # Extract the page path from the event body
        body = json.loads(event.get('body', '{}'))
        page_path = body.get('pagePath', '/')
        
        # If no path is provided, use root path as default
        if not page_path:
            page_path = '/'
            
        # Attempt to increment the counter in DynamoDB
        response = table.update_item(
            Key={
                'pagePath': page_path
            },
            UpdateExpression='ADD #count :increment',
            ExpressionAttributeNames={
                '#count': 'count'
            },
            ExpressionAttributeValues={
                ':increment': Decimal('1')
            },
            ReturnValues='UPDATED_NEW'
        )
        
        # Get the updated count
        count = response.get('Attributes', {}).get('count', 0)
        
        # Return the response with proper CORS headers
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*', # For CORS support
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'count': int(count)  # Convert Decimal to int for JSON serialization
            })
        }
        
    except ClientError as e:
        print(f"DynamoDB error: {e}")
        return error_response("Database error occurred")
    except Exception as e:
        print(f"General error: {e}")
        return error_response("An error occurred processing the request")

def error_response(message):
    return {
        'statusCode': 500,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        'body': json.dumps({
            'success': False,
            'message': message
        })
    }