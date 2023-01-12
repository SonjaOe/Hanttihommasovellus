#!flask/bin/python
import json
from flask import Flask, Response, render_template, request, flash, redirect
from werkzeug.utils import secure_filename
import optparse
import boto3
from boto3.dynamodb.conditions import Key
import uuid
import os
from time import sleep
from datetime import datetime


application = Flask(__name__)
application.secret_key = 'your_secret_key'

def get_datetime():
    try:
        now = datetime.now()
        time = now.strftime("%Y-%m-%d, %H:%M:%S")
        return time
    except:
        return f'Something went wrong'

def upload_to_s3(file, id):
    s3 = boto3.client('s3',region_name='eu-central-1')
    bucket_name = "handyhub"
    try:
        filename =  id + ".png"
        file.save(filename)
        s3.upload_file(
                    Bucket = bucket_name,
                    Filename=filename,
                    Key = filename
                )
        os.remove(filename)
        
    except Exception as e:
        print("Something Happened: ", e)
        return e

    return 


def get_jobs_from_dynamodb():
    try:
        dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
        table = dynamodb.Table('HandyHubServices')
        data = table.scan()
        items = data['Items']
        return items
    except:
        return f'Something went wrong'

def get_service_from_dynamodb(ServiceID):
    try:
        dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
        table = dynamodb.Table('HandyHubServices')
        product_info = table.query(KeyConditionExpression=Key('ServiceID').eq(ServiceID))
        data = product_info['Items']
        return data[0]
    except:
        return f'Something went wrong'

def add_job_to_dynamodb(name, email, city, job, reward, message):
    try:
        id = str(uuid.uuid4())
        date = get_datetime()
        dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
        table = dynamodb.Table('HandyHubServices')
        table.put_item(
            Item={
                'ServiceCreated':date,
                'ServiceID':id,
                'ServiceCity':city,
                'ServiceOwnerName':name,
                'ServiceOwnerEmail':email,
                'RequestedJob':job,
                'ServiceReward':reward,
                'ServiceOwnerMessage':message,
                'ServiceVisibility': True,
            }
        )
        return id
    except:
        return f'Something went wrong'

def add_order_to_dynamodb(name, email, message, ServiceID):
    try:
        id = str(uuid.uuid4())
        dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
        table = dynamodb.Table('HandyHubOrders')
        table.put_item(
            Item={
                'OrderID':id,
                'ServiceID': ServiceID,
                'ServiceProviderName':name,
                'ServiceProviderEmail':email,
                'ServiceProviderMessage':message,
            }
        )
        return id
    except:
        return f'Something went wrong'

def remove_service_visibility_from_dynamodb(ServiceID):
    try:
        dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
        table = dynamodb.Table('HandyHubServices')
        table.update_item(
            Key={'ServiceID': ServiceID},
            UpdateExpression="SET ServiceVisibility= :s",
            ExpressionAttributeValues={':s':False},
        )
        return True
    except:
        return f'Something went wrong'

def add_service_visibility_to_dynamodb(ServiceID):
    try:
        dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
        table = dynamodb.Table('HandyHubServices')
        table.update_item(
            Key={'ServiceID': ServiceID},
            UpdateExpression="SET ServiceVisibility= :s",
            ExpressionAttributeValues={':s':True},
        )
        return True
    except:
        return f'Something went wrong'        

def get_order_email_from_dynamodb_and_delete_order_item(ServiceID):
    try:
        dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
        table = dynamodb.Table('HandyHubOrders')
        data = table.scan()
        items = data['Items']
    except:
        return f'Something went wrong'
    try:
        for item in items:
            if item['ServiceID'] == ServiceID:
                # Retalated to delete_item_from_order_table function that doesn't work
                # try:
                #     delete_item_from_order_table(item['OrderID'])
                # except:
                #     return f'Something went wrong'
                return item['ServiceProviderEmail']
    except:
        return f'Something went wrong'

# Doesn't work atm
# def delete_item_from_order_table(ServiceID):
#     try:
#         # Connect to DynamoDB
#         dynamodb = boto3.resource('dynamodb')
#         table = dynamodb.Table('HandyHubOrders', region_name='eu-central-1')

#         # Define the condition for deletion
#         condition = {
#             'Attribute_exists(non_key_attribute)': True,
#             'attribute_not_exists(another_attribute)': True
#         }

#         # Delete the item from the table
#         table.delete_item(Key={'ServiceID': ServiceID}, ConditionExpression=condition)
#     except:
#         return f'Something went wrong'

def send_deny_email_to_provider(data_order_email, data_from_service_table):
    # Create an SES client
    client = boto3.client('ses')
    # Set the email parameters
    sender = 'anssi.ylileppala@brightstraining.com'
    recipient = data_order_email
    body1 = '''
    <html>
      <head>
        <style>
          body {
            background-color: #003066;
            color: #ffffff;
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
            color: #ffffff;
            font-size: 24px;
            margin: 10px 0;
          }
          p {
            margin: 0 0 10px;
          }
          a {
            color: #ffffff;
            text-decoration: none;
          }
          a:hover {
            color: #ffc107;
          }
        </style>
      </head>
      '''
    body3 = f'''  
      <body>
        <div class="container">
            <h1>Unfortunaly your kind offer to {data_from_service_table['RequestedJob']} has been denied this time.</h1>
            <br>
            <br>
            <br>
            <p><b>Sincerely,</p> 
            <p>the whole HandyHub team</b></p>
            <img src="https://handyhub.s3.eu-central-1.amazonaws.com/images/handyhub-high-resolution-color-logo100x100.png" alt="HandyHub">

        </div>
      </body>
    </html>
    '''
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
            'Data': f"Your offer to {data_from_service_table['RequestedJob']} has been denied"
        },
        'Body': {
            'Html': {
                'Data': body_service_provider
            }
        }
    }
    )


@application.route('/', methods = ['GET', 'POST'])
@application.route('/home', methods = ['GET', 'POST'])
def home_page():
    if request.method == 'POST':
        file = request.files['file']
        name = request.form['name']
        email = request.form['email']
        city = request.form['city']
        job = request.form['job']
        reward = request.form['reward']
        message = request.form['message']
        if file and name and email and city and job and reward and message:
            # Do something with the username and password
            try:
                id = add_job_to_dynamodb(name, email, city, job, reward, message)
                upload_to_s3(file, id)
            except:
                print('Something went wrong')
            flash('Information added successfully!')
            render_template('home.html')
        else:
            flash('Error: All fields are required')
        
    return render_template('home.html')


@application.route('/jobs')
def jobs_page():
    try:
        items = get_jobs_from_dynamodb()
    except:
        return f'Something went wrong'
    sort = request.args.get('sort')
    order = request.args.get('order')
    if sort == 'area':
        items = sorted(items, reverse= True, key=lambda x: x['ServiceCity'])
    elif sort == 'name':
        items = sorted(items, reverse= True, key=lambda x: x['RequestedJob'])
    elif sort == 'posted':
        items = sorted(items, reverse= True, key=lambda x: x.get('ServiceCreated', "2022-01-11, 15:49:15"))
    else:
        # Sort by some default field if no 'sort' parameter is provided
        items = sorted(items, reverse= True, key=lambda x: x['ServiceCreated'])
    if order == 'desc':
        items = list(reversed(items))

    # Render the template
    return render_template('jobs.html', items=items)



@application.route('/jobs/details/<ServiceID>', methods = ['GET', 'POST'])
def details_page(ServiceID):
    data = get_service_from_dynamodb(ServiceID)

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        if name and email and message:
            # Do something with the username and password
            try:
                add_order_to_dynamodb(name, email, message, ServiceID)
                remove_service_visibility_from_dynamodb(ServiceID)
                flash('Job accepted successfully!')
                sleep(1.5)
                return redirect('/jobs')
            except:
                print('Something went wrong')
            
        else:
            flash('Error: All fields are required')
    
    return render_template('details.html', data=data, ServiceID=ServiceID)

@application.route('/jobs/deny/<ServiceID>', methods = ['GET'])
def deny_page(ServiceID):
    try:
        data = get_service_from_dynamodb(ServiceID)
        add_service_visibility_to_dynamodb(ServiceID)
        data_order_email = get_order_email_from_dynamodb_and_delete_order_item(ServiceID)
        send_deny_email_to_provider(data_order_email, data)
    except:
        print('Something went wrong')
    
    return render_template('deny.html', data=data, ServiceID=ServiceID)


if __name__ == '__main__':
    default_port = "80"
    default_host = "0.0.0.0"
    parser = optparse.OptionParser()
    parser.add_option("-H", "--host",
                      help=f"Hostname of Flask app {default_host}.",
                      default=default_host)

    parser.add_option("-P", "--port",
                      help=f"Port for Flask app {default_port}.",
                      default=default_port)

    parser.add_option("-d", "--debug",
                      action="store_true", dest="debug",
                      help=optparse.SUPPRESS_HELP)

    options, _ = parser.parse_args()

    application.run(
        debug=options.debug,
        host=options.host,
        port=int(options.port)
    )
