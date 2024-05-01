import json
import logging
import os

from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from mindee import Client, PredictResponse, product
import pymongo
import requests


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# load credentials and configuration options from .env file
# if you do not yet have a file named .env, make one based on the templatpip e in env.example
load_dotenv()  # take environment variables from .env.

# instantiate the app
app = Flask(__name__)
app.secret_key = 'a_unique_and_secret_key'
# # turn on debugging if in development mode
if os.getenv("FLASK_ENV", "development") == "development":
#     # turn on debugging, if in development
    app.debug = True  # debug mnode

# connect to the database
cxn = pymongo.MongoClient(os.getenv("MONGO_URI"))
db = cxn[os.getenv("MONGO_DBNAME")]  # store a reference to the database

@app.route('/predict', methods=['POST'])
def pretdict_endpoint():
    # Get the image data from the request
    request_data = request.get_json()  # Extract JSON data from the request
    if 'Object_ID' not in request_data:
        return jsonify({'error': 'Object_ID not found in request data'}), 400
    
    Object_ID = ObjectId(request_data['Object_ID']) 
    logging.debug('OBJECT_ID MESSAGE:', Object_ID)
    #image = db.receipts.find_one({"_id": Object_ID})['image']

    # Here, you would add the code to perform OCR on the image
    # For now, let's assume you have a function called perform_ocr that does this
    
    # Uncomment next line to perform OCR
    data = perform_ocr(Object_ID)
    logging.debug("data after ocr: %s", data) # debug
    print("data after ocr: %s", data)
    #data = json.load(open("response1.json", "r"))

    # Connect to your collection (replace 'mycollection' with your collection name)
    collection = db['receipts']

    # Prepare the data to be inserted into the database
    # line_items = data['document']['inference']['pages'][0]['prediction']['line_items']
    receipt = data['document']['inference']['pages'][0]['prediction']
    logging.debug('OCR Json Keys:', data['document']['inference']['pages'][0]['prediction'].keys()) # debug
    print('OCR Json Keys:', data['document']['inference']['pages'][0]['prediction'].keys())
    receipt_data = {
        'receipt_name': receipt['supplier_name']['raw_value'],
        'currency': receipt['locale']['currency'],
        'items': [{'description': item['description'], 'amount': item['total_amount'], 'quantity': item['quantity']} for item in receipt['line_items']],
        'total': receipt['total_amount']['value'],
        'tax': receipt['total_tax']['value'],
        'tip': receipt['tip']['value'],
        'subtotal': receipt['total_net']['value'],
    }
    logging.debug(receipt_data)
    print("receipt_data: %s", receipt_data)

    # Update the document with given ObjectId
    collection.update_one({'_id': Object_ID}, {'$set': receipt_data})
    inserted_id = Object_ID

    # Return the inserted_id as a JSON response
    return jsonify({'_id': str(inserted_id)})

def perform_ocr(Object_ID):
    logging.debug("starting perform_ocr function with mindee api...") # debug
    url = "https://api.mindee.net/v1/products/mindee/expense_receipts/v5/predict"
    api_key = os.getenv("OCR_API_KEY")  # Get the API key from environment variable

    # Fetch the image data from the database
    image_data = db.receipts.find_one({"_id": Object_ID})['image']
    file_path = f"receipt_{Object_ID}.jpg"  # Set the file path to save the image
    logging.debug("file path: %s", file_path) # debug

    # Save the image data to a file
    with open(file_path, "wb") as f:
        f.write(image_data)
    
    # Parse the file with the Mindee API
    with open(file_path, "rb") as myfile:
        files = {"document": myfile}
        headers = {"Authorization": "Token " + api_key}
        response = requests.post(url, files=files, headers=headers)
        print("Type of response: ", type(response))
        print("response.text: %s", response.text)
        return response.json()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)  # Run the app