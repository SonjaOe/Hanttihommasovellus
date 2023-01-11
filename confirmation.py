import boto3
from boto3.dynamodb.conditions import Key

def extract_key_value_pairs(event):
    data = {}
    for record in event['Records']:
        new_image = record['dynamodb']['NewImage']
        for key, value in new_image.items():
            data[key] = value['S']
    return data
# Extract the key-value pairs from the event

def query_dynamodb_service_table(ServiceID):
    dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
    table = dynamodb.Table('HandyHubServices')
    product_info = table.query(KeyConditionExpression=Key('ServiceID').eq(ServiceID))
    data_from_service_table = product_info['Items']
    return data_from_service_table[0]

def lambda_handler(event, context):
    data = extract_key_value_pairs(event)

    data_from_service_table = query_dynamodb_service_table(data['ServiceID'])

    # Create an SES client
    client = boto3.client('ses')
    # Set the email parameters
    sender = 'anssi.ylileppala@brightstraining.com'
    recipient = data_from_service_table['ServiceOwnerEmail']
    recipient2 = data['ServiceProviderEmail']
    body1 = '''
    <html>
      <head>
        <style>
          body {
            background-color: #ffc107;
            color: #333;
            font-family: sans-serif;
            margin: 0;
            padding: 0;
          }
          .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            text-align: center;
          }
          h1 {
            color: #333;
            font-size: 24px;
            margin: 10px 0;
          }
          p {
            margin: 0 0 10px;
          }
          a {
            color: #333;
            text-decoration: none;
          }
          a:hover {
            color: #ffc107;
          }
        </style>
      </head>
      '''
    body2 = f'''  
      <body>
        <div class="container">
            <h1>Congratulations {data_from_service_table['ServiceOwnerName']}!</h1>
            <p>{data['ServiceProviderName']} has accepted your job offer with following message attached: {data['ServiceProviderMessage']}</p>
            <p>Job details ID: {data['ServiceID']}</p>
            <p>{data_from_service_table['RequestedJob']}, Payment {data_from_service_table['ServiceReward']}, location: {data_from_service_table['ServiceCity']}.</p>
            <p>{data['ServiceProviderName']}'s contact info below. </p>
            <p>{data['ServiceProviderName']}, {data['ServiceProviderEmail']} </p>
            <p>Please contact {data['ServiceProviderName']} regarding the details of the job, such as the address and a suitable time.</p>
            <br>
            <br>
            <p>Sincerely,</p> 
            <p>the whole HandyHub team</p>
            <img src="https://handyhub.s3.eu-central-1.amazonaws.com/images/handy_hub_100x100.png" alt="HandyHub">

        </div>
      </body>
    </html>
    '''

    body3 = f'''  
      <body>
        <div class="container">
            <h1>Congratulations {data['ServiceProviderName']}!</h1>
            <p>You have succesfully accepted {data_from_service_table['ServiceOwnerName']}'s job offer.</p>
            <p>Job details ID: {data['ServiceID']}</p>
            <p>{data_from_service_table['RequestedJob']}, Reward {data_from_service_table['ServiceReward']}, location: {data_from_service_table['ServiceCity']}.</p>
            <p>Please see {data_from_service_table['ServiceOwnerName']}'s contact info below. </p>
            <p>{data_from_service_table['ServiceOwnerName']}, {data_from_service_table['ServiceOwnerEmail']} </p>
            <p>Please contact {data_from_service_table['ServiceOwnerName']} regarding the details of the job, such as the address and a suitable time.</p>
            <br>
            <br>
            <p>Sincerely,</p> 
            <p>the whole HandyHub team</p>
            <img src="https://handyhub.s3.eu-central-1.amazonaws.com/images/handy_hub_100x100.png" alt="HandyHub">

        </div>
      </body>
    </html>
    '''
    
    body_service_owner = body1 + body2
    body_service_provider = body1 + body3
    # Send the email to Service orderer
    response = client.send_email(
      Source=sender,
      Destination={
          'ToAddresses': [
              recipient,
          ]
      },
      Message={
          'Subject': {
              'Data': f"{data['ServiceProviderName']} accepted your offer to complete the job"
          },
          'Body': {
              'Html': {
                  'Data': body_service_owner
              }
          }
      }
    )

    response2 = client.send_email(
      Source=sender,
      Destination={
          'ToAddresses': [
              recipient2,
          ]
      },
      Message={
          'Subject': {
              'Data': f"You accepted to complete {data_from_service_table['ServiceOwnerName']}'s job"
          },
          'Body': {
              'Html': {
                  'Data': body_service_provider
              }
          }
      }
    )
    
    # Print the response
    print(event)




