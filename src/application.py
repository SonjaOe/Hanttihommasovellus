#!flask/bin/python
import json
from flask import Flask, Response, render_template, request, flash
import optparse
import boto3
from boto3.dynamodb.conditions import Key
import uuid
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
            try:
                add_job_to_dynamodb(name, email, city, job, reward, message)
            except:
                print('Something went wrong')
            flash('Information added successfully!')
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
        items = sorted(items, key=lambda x: x['ServiceCity'])
    elif sort == 'name':
        items = sorted(items, key=lambda x: x['RequestedJob'])
    elif sort == 'posted':
        items = sorted(items, key=lambda x: x['ServiceCreated'])
    else:
        # Sort by some default field if no 'sort' parameter is provided
        items = sorted(items, key=lambda x: x['RequestedJob'])
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
            except:
                print('Something went wrong')
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
