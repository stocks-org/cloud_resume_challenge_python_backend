import unittest
import json
import os
from unittest.mock import patch, MagicMock
from decimal import Decimal

# Set AWS region for boto3 before importing index
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

# Import the module to test
import index

class TestLambdaFunction(unittest.TestCase):
    """Test class for the page hit counter Lambda function."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Ensure the environment variable exists for tests
        if 'TABLE_NAME' not in os.environ:
            os.environ['TABLE_NAME'] = 'PageHitCounters'

    @patch('index.table')
    def test_lambda_handler_success(self, mock_table):
        """Test successful incrementing of a page counter."""
        # Mock the DynamoDB response
        mock_response = {
            'Attributes': {
                'count': Decimal('5')
            }
        }
        mock_table.update_item.return_value = mock_response
        
        # Create a test event
        event = {
            'body': json.dumps({
                'pagePath': '/test-page'
            })
        }
        
        # Execute the lambda handler
        response = index.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 200)
        self.assertTrue(json.loads(response['body'])['success'])
        self.assertEqual(json.loads(response['body'])['count'], 5)
        
        # Verify that update_item was called with correct parameters
        mock_table.update_item.assert_called_once_with(
            Key={
                'pagePath': '/test-page'
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
    
    @patch('index.table')
    def test_lambda_handler_default_path(self, mock_table):
        """Test using the default path when none is provided."""
        # Mock the DynamoDB response
        mock_response = {
            'Attributes': {
                'count': Decimal('1')
            }
        }
        mock_table.update_item.return_value = mock_response
        
        # Create a test event with empty pagePath
        event = {
            'body': json.dumps({
                'pagePath': ''
            })
        }
        
        # Execute the lambda handler
        response = index.lambda_handler(event, {})
        
        # Verify the path defaults to '/'
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args[1]
        self.assertEqual(call_args['Key']['pagePath'], '/')
    
    @patch('index.table')
    def test_lambda_handler_no_body(self, mock_table):
        """Test handling an event with no body."""
        # Mock the DynamoDB response
        mock_response = {
            'Attributes': {
                'count': Decimal('1')
            }
        }
        mock_table.update_item.return_value = mock_response
        
        # Create a test event with no body
        event = {}
        
        # Execute the lambda handler
        response = index.lambda_handler(event, {})
        
        # Verify the path defaults to '/'
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args[1]
        self.assertEqual(call_args['Key']['pagePath'], '/')
    
    @patch('index.table')
    def test_lambda_handler_dynamo_error(self, mock_table):
        """Test handling a DynamoDB ClientError."""
        # Mock DynamoDB to raise a ClientError
        from botocore.exceptions import ClientError
        mock_table.update_item.side_effect = ClientError(
            error_response={'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Table not found'}},
            operation_name='UpdateItem'
        )
        
        # Create a test event
        event = {
            'body': json.dumps({
                'pagePath': '/test-page'
            })
        }
        
        # Execute the lambda handler
        response = index.lambda_handler(event, {})
        
        # Verify the error response
        self.assertEqual(response['statusCode'], 500)
        self.assertFalse(json.loads(response['body'])['success'])
        self.assertEqual(json.loads(response['body'])['message'], 'Database error occurred')
    
    @patch('index.table')
    def test_lambda_handler_general_exception(self, mock_table):
        """Test handling a general exception."""
        # Mock DynamoDB to raise a general exception
        mock_table.update_item.side_effect = Exception('Test exception')
        
        # Create a test event
        event = {
            'body': json.dumps({
                'pagePath': '/test-page'
            })
        }
        
        # Execute the lambda handler
        response = index.lambda_handler(event, {})
        
        # Verify the error response
        self.assertEqual(response['statusCode'], 500)
        self.assertFalse(json.loads(response['body'])['success'])
        self.assertEqual(json.loads(response['body'])['message'], 'An error occurred processing the request')
    
    def test_error_response(self):
        """Test the error_response helper function."""
        response = index.error_response("Test error message")
        
        # Verify the structure of the error response
        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(response['headers']['Access-Control-Allow-Origin'], '*')
        self.assertFalse(json.loads(response['body'])['success'])
        self.assertEqual(json.loads(response['body'])['message'], 'Test error message')


if __name__ == '__main__':
    # Run the tests before executing the main script
    unittest.main()