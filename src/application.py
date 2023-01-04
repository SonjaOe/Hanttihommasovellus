#!flask/bin/python
import json
from flask import Flask, Response, render_template, request, flash
import optparse
import boto3
from boto3.dynamodb.conditions import Key
import uuid

application = Flask(__name__)
application.secret_key = 'your_secret_key'



def get_jobs_from_dynamodb():
    dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
    table = dynamodb.Table('HelpHubServicesTest')
    data = table.scan()
    items = data['Items']
    return items

def get_service_from_dynamodb(ServiceID):
    # dynamodb = boto3.client('dynamodb', region_name='eu-central-1')
    # data = dynamodb.get_item(
    #     TableName='HelpHubServicesTest',
    #     Key={
    #         'ServiceID': {
    #             'S': ServiceID
    #         }
    #     }
    #     )
    dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
    table = dynamodb.Table('HelpHubServicesTest')
    product_info = table.query(KeyConditionExpression=Key('ServiceID').eq(ServiceID))
    data = product_info['Items']
    # newstock = int(data[0]['ProdStock'])-1
    # table.update_item(
    #     Key={'ProdCat': ProdCat,'ProdName': ProdName},
    #     UpdateExpression="SET ProdStock= :s",
    #     ExpressionAttributeValues={':s':newstock},
    # )
    return data[0]

def add_job_to_dynamodb(name, email, city, job, reward, message):
    id = str(uuid.uuid4())
    dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
    table = dynamodb.Table('HelpHubServicesTest')
    # table.update_item(
    #     Key={'OrderID': id},
    #     UpdateExpression="SET ProdName= :s",
    #     ExpressionAttributeValues={':s': name},
    # )
    table.put_item(
        TableName="HelpHubServicesTest",
        Item={
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

def add_order_to_dynamodb(name, email, message, ServiceID):
    id = str(uuid.uuid4())
    dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
    table = dynamodb.Table('HelpHubOrdersTest')
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

def remove_service_visibility_from_dynamodb(ServiceID):
    dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
    table = dynamodb.Table('HelpHubServicesTest')
    table.update_item(
        Key={'ServiceID': ServiceID},
        UpdateExpression="SET ServiceVisibility= :s",
        ExpressionAttributeValues={':s':False},
    )
    return True

@application.route('/', methods = ['GET', 'POST'])
@application.route('/home', methods = ['GET', 'POST'])
def home_page():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        city = request.form['city']
        job = request.form['job']
        reward = request.form['reward']
        message = request.form['message']
        if name and email and city and job and reward and message:
            # Do something with the username and password
            add_job_to_dynamodb(name, email, city, job, reward, message)
            flash('Information added successfully!')
        else:
            flash('Error: All fields are required')
        
    return render_template('home.html')

@application.route('/market')
def market_page():
    items = get_jobs_from_dynamodb()
    return render_template('market.html', items=items)

@application.route('/market/details/<ServiceID>', methods = ['GET', 'POST'])
def details_page(ServiceID):
    data = get_service_from_dynamodb(ServiceID)

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        if name and email and message:
            # Do something with the username and password
            add_order_to_dynamodb(name, email, message, ServiceID)
            remove_service_visibility_from_dynamodb(ServiceID)
            flash('Information added successfully!')
        else:
            flash('Error: All fields are required')
    
    return render_template('details.html', data=data)


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
