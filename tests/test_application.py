import json
import pytest
import boto3
from src.application import application

@pytest.fixture
def client():
    return application.test_client()

def test_request_home_page(client):
    response = client.get('/home')
    assert response.status_code == 200
    assert b"Welcome to the HandyHub" in response.data

def test_request_market_page(client):
    response = client.get('/jobs')
    assert response.status_code == 200