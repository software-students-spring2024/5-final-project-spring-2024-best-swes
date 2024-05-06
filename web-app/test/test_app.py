import pytest
from flask import url_for
import os
import tempfile
import io
from unittest.mock import patch
import sys
from pathlib import Path
import mongomock
import requests_mock
from bson import ObjectId

# Adjust the Python path to include the directory above the 'test' directory where 'app.py' is located
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent  # 'web_app' directory
sys.path.insert(0, str(parent_dir))

from app import app  # Now you can successfully import app
from app import call_ml_service  # Assuming call_ml_service is in app.py

# Use a valid ObjectId for tests
test_id = str(ObjectId())


@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
    with app.test_client() as client:
        yield client
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def mock_db(monkeypatch):
    mock_client = mongomock.MongoClient()
    monkeypatch.setattr('pymongo.MongoClient', lambda *args, **kwargs: mock_client)
    db = mock_client['test_db']  # simulate the database
    # Now simulate collections within this database
    db.create_collection("receipts")
    db.create_collection("images")
    return db

@pytest.fixture
def mock_requests(monkeypatch):
    """
    Create a fixture that mocks requests.post method to prevent actual HTTP calls in tests.
    """
    with requests_mock.Mocker() as m:
        monkeypatch.setattr("requests.post", m.post)
        yield m

@pytest.fixture
def prepare_data(mock_db):
    """Prepare the database with dummy data."""
    receipt_id = ObjectId()
    mock_db.receipts.insert_one({
        "_id": receipt_id,
        "names": ["Alice", "Bob"],
        "items": [
            {"_id": ObjectId(), "description": "Salad", "price": 10.00, "is_appetizer": True},
            {"_id": ObjectId(), "description": "Steak", "price": 25.00, "is_appetizer": False}
        ],
        "allocations": [
            {"name": "Alice", "items": ["Salad"]},
            {"name": "Bob", "items": ["Steak"]}
        ],
        "num_of_people": 2
    })
    return receipt_id

def test_home_page_status(client):
    response = client.get('/')
    assert response.status_code == 200
    
def test_upload_image_no_file(client):
    """Test uploading an image with no file attached."""
    response = client.post('/upload', data={})
    assert response.status_code == 400
    assert 'No image part' in response.data.decode()

def test_numofpeople_route(client, prepare_data):
    """Test the numofpeople page loads correctly."""
    response = client.get(f'/numofpeople/{prepare_data}')
    assert response.status_code == 200
    assert 'Enter Number of People and Names' in response.data.decode()

def test_post_appetizers_selection(client, mock_db, prepare_data):
    """Test updating appetizers selection."""
    appetizer_id = str(ObjectId())  # Simulating an appetizer ID
    data = {'appetizers': [appetizer_id]}
    response = client.post(f'/select_appetizers/{prepare_data}', data=data)
    assert response.status_code == 302  # Expect redirection after successful post
    assert '/allocateitems/' in response.headers['Location']

def test_finalize_allocation(client, mock_db, prepare_data):
    """Test finalizing the item allocation updates the database correctly."""
    data = {'item_123456': ['John', 'Jane']}
    response = client.post(f'/allocateitems/{prepare_data}', data=data)
    assert response.status_code == 302  # Check for redirection
    assert '/enter_tip/' in response.headers['Location']

def test_enter_tip_page(client, prepare_data):
    """Test loading the tip entry page."""
    response = client.get(f'/enter_tip/{prepare_data}')
    assert response.status_code == 200
    assert 'Enter Tip Percentage' in response.data.decode()

def test_post_tip_percentage(client, prepare_data):
    """Test posting the tip percentage redirects to bill calculation."""
    data = {'tip_percentage': '15'}
    response = client.post(f'/enter_tip/{prepare_data}', data=data)
    assert response.status_code == 302
    assert '/calculate_bill/' in response.headers['Location']

def test_search_history_page(client):
    """Test the search history page loads properly."""
    response = client.get('/search_history')
    assert response.status_code == 200
    assert 'Receipt History' in response.data.decode()

def test_history_search_function(client, prepare_data):
    """Test the history search functionality."""
    response = client.get(f'/history?search={prepare_data}')
    assert response.status_code == 200
    assert 'Search Results' in response.data.decode()

def test_allocate_items_no_selection(client, prepare_data):
    """Test posting allocate items with no selection leads to no change."""
    response = client.post(f'/allocateitems/{prepare_data}', data={})
    assert response.status_code == 302
    assert '/enter_tip/' in response.headers['Location']

def test_history_with_no_results(client):
    """Test the history page with no matching results."""
    response = client.get('/history?search=nonexistent')
    assert response.status_code == 200
    assert 'No results found.' in response.data.decode()

def test_server_status(client):
    """Test the server status endpoint."""
    response = client.get('/test_connection')
    assert response.status_code == 200
    assert 'Machine Learning Client is reachable' in response.data.decode()

def test_calculate_bill_invalid_input(client, prepare_data):
    """Test handling invalid tip input."""
    data = {'tip_percentage': 'invalid'}
    response = client.post(f'/calculate_bill/{prepare_data}', data=data)
    assert response.status_code == 400
    assert 'Invalid tip percentage provided' in response.data.decode()

def test_history_page_empty_search(client):
    """Test history page functionality with an empty search query."""
    response = client.get('/history?search=')
    assert response.status_code == 200
    assert 'No results found.' not in response.data.decode()

def test_test_connection_endpoint(client):
    """Test the test connection endpoint for expected success response."""
    response = client.get('/test_connection')
    assert response.status_code == 200
    assert 'Machine Learning Client is reachable' in response.data.decode()

def test_allocate_items_submit_without_changes(client, prepare_data):
    """Test submitting the allocation form without any changes to allocations."""
    response = client.post(f'/allocateitems/{prepare_data}', data={})
    assert response.status_code == 302
    assert '/enter_tip/' in response.headers['Location']

def test_allocate_items_submit_with_changes(client, mock_db, prepare_data):
    """Test updating the allocation of items to people."""
    data = {'item_1': ['Alice'], 'item_2': ['Bob']}
    response = client.post(f'/allocateitems/{prepare_data}', data=data)
    assert response.status_code == 302
    assert '/enter_tip/' in response.headers['Location']
    # Check that allocations are updated in the database
    updated_receipt = mock_db.receipts.find_one({"_id": prepare_data})
    assert 'Alice' in updated_receipt['allocations'][0]['name']
    assert 'Bob' in updated_receipt['allocations'][1]['name']

def test_enter_tip_redirects_correctly(client, prepare_data):
    """Test that entering a tip redirects to the calculate bill page correctly."""
    response = client.post(f'/enter_tip/{prepare_data}', data={'tip_percentage': '15'})
    assert response.status_code == 302
    assert 'calculate_bill' in response.headers['Location']

def test_allocate_items_no_selection(client, prepare_data):
    """Test posting allocate items with no selection leads to no change."""
    response = client.post(f'/allocateitems/{prepare_data}', data={})
    assert response.status_code == 302
    assert '/enter_tip/' in response.headers['Location']