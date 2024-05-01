import os
from flask import Flask, request, jsonify
import requests
import pymongo
from pymongo import MongoClient
import json
from dotenv import load_dotenv
from bson import ObjectId

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Use receipt-OCR.py to get response1.json
# (can only do this a couple times an hour with the test API key)

# Load response1.json
with open("response1.json", "r") as f:
    data = json.load(f)

print('Receipt Keys:', data['receipts'][0].keys())
items = data['receipts'][0]['items']
print()
print(f"Your purchase at {data['receipts'][0]['merchant_name']}")

for item in items:
    print(f"{item['description']} - {data['receipts'][0]['currency']} {item['amount']}")
print("-" * 20)
print(f"Subtotal: {data['receipts'][0]['currency']} {data['receipts'][0]['subtotal']}")
print(f"Tax: {data['receipts'][0]['currency']} {data['receipts'][0]['tax']}")
print("-" * 20)
print(f"Total: {data['receipts'][0]['currency']} {data['receipts'][0]['total']}")
# print(data['receipts'])


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

# Load response1.json
with open("response1.json", "r") as f:
    data = json.load(f)

print('Receipt Keys:', data['receipts'][0].keys())
items = data['receipts'][0]['items']
print()
print(f"Your purchase at {data['receipts'][0]['merchant_name']}")

for item in items:
    print(f"{item['description']} - {data['receipts'][0]['currency']} {item['amount']}")
print("-" * 20)
print(f"Subtotal: {data['receipts'][0]['currency']} {data['receipts'][0]['subtotal']}")
print(f"Tax: {data['receipts'][0]['currency']} {data['receipts'][0]['tax']}")
print("-" * 20)
print(f"Total: {data['receipts'][0]['currency']} {data['receipts'][0]['total']}")
# print(data['receipts'])

@app.route('/predict', methods=['POST'])
def pretdict_endpoint():
    # Get the image data from the request
    request_data = request.get_json()  # Extract JSON data from the request
    if 'Object_ID' not in request_data:
        return jsonify({'error': 'Object_ID not found in request data'}), 400
    
    Object_ID = ObjectId(request_data['Object_ID']) 
    logger.debug('OBJECT_ID MESSAGE:', Object_ID)
    #image = db.receipts.find_one({"_id": Object_ID})['image']

    # Here, you would add the code to perform OCR on the image
    # For now, let's assume you have a function called perform_ocr that does this
    
    # Uncomment next line to perform OCR
    data = perform_ocr(Object_ID)
    #data = json.load(open("response1.json", "r"))

    # Connect to your collection (replace 'mycollection' with your collection name)
    collection = db['receipts']

    # Prepare the data to be inserted into the database
    receipt = data['receipts'][0]
    receipt_data = {
        'receipt_name': receipt['merchant_name'],
        'currency': receipt['currency'],
        'items': [{'description': item['description'], 'amount': item['amount']} for item in receipt['items']],
        'total': receipt['total'],
        'tax': receipt['tax'],
        'tip': receipt['tip'],
        'subtotal': receipt['subtotal'],
    }
    logger.debug(receipt_data)

    # Update the document with given ObjectId
    collection.update_one({'_id': Object_ID}, {'$set': receipt_data})
    inserted_id = Object_ID

    # Return the inserted_id as a JSON response
    return jsonify({'_id': str(inserted_id)})

def perform_ocr():
    try:
        json_file_path = os.path.join(os.path.dirname(__file__), 'response1.json')
        with open(json_file_path, "r") as file:
            data = json.load(file)
        if 'receipts' in data and len(data['receipts']) > 0:
            # Access the first receipt since the JSON has an array of receipts
            receipt_data = data['receipts'][0]

            # Prepare the receipt format as needed, you might need to adjust based on your MongoDB schema
            formatted_receipt = {
                'merchant_name': receipt_data.get('merchant_name'),
                'merchant_address': receipt_data.get('merchant_address'),
                'merchant_phone': receipt_data.get('merchant_phone'),
                'total': receipt_data.get('total'),
                'tax': receipt_data.get('tax'),
                'subtotal': receipt_data.get('subtotal'),
                'currency': receipt_data.get('currency'),
                'items': receipt_data.get('items', []),
                'date': receipt_data.get('date')
            }
            return formatted_receipt
        else:
            logger.error("No 'receipts' key found in JSON file or 'receipts' array is empty.")
            return None
    except FileNotFoundError:
        logger.error(f"The file {json_file_path} was not found.")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in file {json_file_path}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return None




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)  # Run the app