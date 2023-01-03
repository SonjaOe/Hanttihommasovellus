#!flask/bin/python
import json
from flask import Flask, Response, render_template, request
import optparse
import boto3
from boto3.dynamodb.conditions import Key
import uuid

application = Flask(__name__)


def get_products_from_dynamodb():
    dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
    table = dynamodb.Table('W10Group1Product')
    data = table.scan()
    items = data['Items']
    return items

def subtract_products_from_dynamodb(ProdCat,ProdName):
    dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
    table = dynamodb.Table('W10Group1Product')
    product_info = table.query(KeyConditionExpression=Key('ProdCat').eq(ProdCat) & Key('ProdName').eq(ProdName))
    data = product_info['Items']
    newstock = int(data[0]['ProdStock'])-1
    table.update_item(
        Key={'ProdCat': ProdCat,'ProdName': ProdName},
        UpdateExpression="SET ProdStock= :s",
        ExpressionAttributeValues={':s':newstock},
    )
    return str(newstock)

def add_order_to_to_dynamodb(ProdName):
    id = str(uuid.uuid4())
    OrderNumber = str('ORD#' + id)
    dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
    table = dynamodb.Table('W10Group1UsersOrders')
    table.update_item(
        Key={'PrimaryAccountID': 'ACC#007','SortKey': OrderNumber},
        UpdateExpression="SET ProdName= :s",
        ExpressionAttributeValues={':s':ProdName},
    )
    return OrderNumber

@application.route('/')
@application.route('/home')
def home_page():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        # Do something with the username and password
        add_order_to_to_dynamodb(name)
    return render_template('home.html')

@application.route('/market')
def market_page():
    items = get_products_from_dynamodb()
    return render_template('market.html', items=items)

@application.route('/market/purchase/<ProdCat>/<ProdName>')
def purchase_page(ProdCat,ProdName):
    data = subtract_products_from_dynamodb(ProdCat,ProdName)
    OrderNumber = add_order_to_to_dynamodb(ProdName)
    return render_template('purchase.html', data=data, ProdName = ProdName, OrderNumber = OrderNumber)


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
