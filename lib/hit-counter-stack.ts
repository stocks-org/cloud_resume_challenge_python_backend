import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as path from 'path';

export class HitCounterStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create DynamoDB table for hit counter
    const hitCounterTable = new dynamodb.Table(this, 'PageHitCounters', {
      partitionKey: {
        name: 'pagePath',
        type: dynamodb.AttributeType.STRING
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // Deletes the table when the stack is deleted
    });

    // Lambda function for hit counter
    const hitCounterFunction = new lambda.Function(this, 'HitCounterFunction', {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'index.lambda_handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda')), // Assumes code is in a 'lambda' directory
      environment: {
        TABLE_NAME: hitCounterTable.tableName,
      },
      timeout: cdk.Duration.seconds(10),
      memorySize: 128,
    });

    // Grant Lambda permissions to read and write to DynamoDB
    hitCounterTable.grantReadWriteData(hitCounterFunction);

    // Create API Gateway
    const api = new apigateway.RestApi(this, 'HitCounterApi', {
      restApiName: 'Hit Counter Service',
      description: 'API for incrementing page hit counters',
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type', 'X-Amz-Date', 'Authorization', 'X-Api-Key'],
        maxAge: cdk.Duration.days(1),
      }
    });

    // Create API Gateway resource and method
    const incrementResource = api.root.addResource('incrementCounter');
    incrementResource.addMethod('POST', new apigateway.LambdaIntegration(hitCounterFunction));

    // Output the API URL
    new cdk.CfnOutput(this, 'ApiUrl', {
      value: api.url,
      description: 'URL of the API Gateway endpoint',
    });
  }
}