#1 imports - For room booking - Boto3, json and uuid
import json
import boto3
import uuid

#2 Create a client connection -  https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html
client = boto3.client('dynamodb')

#3 Store the user input - Print the event details from agent
def lambda_handler(event, context):
    print(f"The user input from Agent is {event}")
    input_data = event

    #4. Get all items from hack-aranda-myobb-silverfine-table using scan method https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/scan.html
    response = client.scan(TableName='hack-aranda-myobb-silverfine-table')
    print(response)

    #5. Check if any items exist in the database
    if 'Items' not in response or len(response['Items']) == 0:
        # Create proper Bedrock Agent error response for no data found
        error_response_body = {
            'application/json': {
                'body': json.dumps({'error': 'No transactions data found in the database.'})
            }
        }
        
        action_response = {
            'actionGroup': event['actionGroup'],
            'apiPath': event['apiPath'],
            'httpMethod': event['httpMethod'],
            'httpStatusCode': 404,
            'responseBody': error_response_body
        }
        
        session_attributes = event['sessionAttributes']
        prompt_session_attributes = event['promptSessionAttributes']
        
        api_response = {
            'messageVersion': '1.0', 
            'response': action_response,
            'sessionAttributes': session_attributes,
            'promptSessionAttributes': prompt_session_attributes
        }
        
        print(f"No data found in database. Returning error response: {api_response}")
        return api_response
        
    myobb_silverfine_data = response['Items']
    print(myobb_silverfine_data)


    #6 Check if this is a Bedrock Agent call or direct test call
    if 'agent' in event and 'actionGroup' in event:
        # This is a Bedrock Agent call - return proper agent response
        agent = event['agent']
        actionGroup = event['actionGroup']
        api_path = event['apiPath']

        response_body = {
            'application/json': {
                'body': json.dumps(myobb_silverfine_data)
            }
        }
        
        action_response = {
            'actionGroup': event['actionGroup'],
            'apiPath': event['apiPath'],
            'httpMethod': event['httpMethod'],
            'httpStatusCode': 200,
            'responseBody': response_body
        }
        
        session_attributes = event['sessionAttributes']
        prompt_session_attributes = event['promptSessionAttributes']
        
        #https://docs.aws.amazon.com/bedrock/latest/userguide/agents-lambda.html#agents-lambda-example
        api_response = {
            'messageVersion': '1.0', 
            'response': action_response,
            'sessionAttributes': session_attributes,
            'promptSessionAttributes': prompt_session_attributes
        }
        
        return api_response
    else:
        # This is a direct lambda test call - return simple response
        # https://docs.aws.amazon.com/bedrock/latest/userguide/agents-lambda.html#agents-lambda-example
        print("Direct lambda test call detected - returning simple response")
        # Create similar structure to line 77 for consistency
        response_body = {
            'application/json': {
                'body': json.dumps({
                    'message': 'Successfully retrieved transactions data',
                    'data': myobb_silverfine_data,
                    'count': len(myobb_silverfine_data)
                })
            }
        }
        
        action_response = {
            'actionGroup': '',
            'apiPath': '',
            'httpMethod': '',
            'httpStatusCode': 200,
            'responseBody': response_body
        }
        
        api_response = {
            'messageVersion': '1.0', 
            'response': action_response,
            'sessionAttributes': {},
            'promptSessionAttributes': {}
        }
        
        return api_response
