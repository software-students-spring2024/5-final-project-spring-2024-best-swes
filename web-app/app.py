import os
from flask import Flask, render_template, redirect, request, url_for, jsonify
import pymongo
from pymongo import MongoClient
from werkzeug.utils import secure_filename
import requests
from dotenv import load_dotenv
from bson import ObjectId
import json
import uuid

import logging

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
#     # turn on d   ebugging, if in development
    app.debug = True  # debug mnode

# connect to the database
cxn = pymongo.MongoClient(os.getenv("MONGO_URI"))
db = cxn[os.getenv("MONGO_DBNAME")]  # store a reference to the database

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
            for item in receipt_data.get('items', []):
                item['_id'] = str(uuid.uuid4())  # Assign a unique ID
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



#homepage -add receipt - history 
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image part"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Simulate OCR by loading data from a JSON file
    receipt_data = perform_ocr()
    if not receipt_data:
        return jsonify({"error": "OCR simulation failed or JSON file is incorrect"}), 500

    # Insert parsed data into MongoDB
    result = db.receipts.insert_one(receipt_data)
    inserted_id = str(result.inserted_id)
    return redirect(url_for('numofpeople', receipt_id=inserted_id))


#(  pull receipt from database )
@app.route('/numofpeople/<receipt_id>')
def numofpeople(receipt_id):
    """
    Display the form to enter the number of people and their names.
    """
    return render_template("numofpeople.html", receipt_id=receipt_id)

@app.route('/submit_people/<receipt_id>', methods=["POST"])
def submit_people(receipt_id):
    """
    Process the submitted number of people and names.
    """
    count = request.form['count']
    names = request.form['names']
    # Split the names by comma and strip spaces
    names_list = [name.strip() for name in names.split(',')]

    try:
        # Update the existing document in the receipts collection
        db.receipts.update_one({"_id": ObjectId(receipt_id)}, {"$set": {"num_of_people": count, "names": names_list}})
        return redirect(url_for('select_appetizers', receipt_id=receipt_id))
         # Redirect to another page after submission
    except pymongo.errors.ServerSelectionTimeoutError as e:
        logger.error("Could not connect to MongoDB: %s", str(e))
        return jsonify({"error": "Database connection failed"}), 503
#label appetizers

def is_valid_uuid(uuid_to_test, version=4):
    try:
        uuid_obj = uuid.UUID(uuid_to_test, version=version)
        return str(uuid_obj) == uuid_to_test
    except ValueError:
        return False

@app.route('/select_appetizers/<receipt_id>', methods=['GET', 'POST'])
def select_appetizers(receipt_id):
    if request.method == 'POST':
        if 'no_appetizers' in request.form and request.form['no_appetizers'] == 'none':
            logging.debug("No appetizers selected by user.")
            db.receipts.update_one(
                {'_id': ObjectId(receipt_id)},
                {'$set': {'items.$[].is_appetizer': False}}  # Reset all items to not be appetizers
            )
            return redirect(url_for('allocateitems', receipt_id=receipt_id))

        appetizer_ids = request.form.getlist('appetizers')
        logging.debug(f"Received appetizer IDs: {appetizer_ids}")

        valid_ids = [id for id in appetizer_ids if is_valid_uuid(id)]
        logging.debug(f"Valid appetizer IDs: {valid_ids}")

        if valid_ids:
            # Update items where the ID matches any of the valid appetizer IDs
            db.receipts.update_many(
                {'_id': ObjectId(receipt_id), 'items._id': {'$in': valid_ids}},
                {'$set': {'items.$.is_appetizer': True}}
            )
            # Reset is_appetizer for other items
            db.receipts.update_many(
                {'_id': ObjectId(receipt_id), 'items._id': {'$nin': valid_ids}},
                {'$set': {'items.$.is_appetizer': False}}
            )
        else:
            db.receipts.update_one(
                {'_id': ObjectId(receipt_id)},
                {'$set': {'items.$[].is_appetizer': False}}
            )

        return redirect(url_for('allocateitems', receipt_id=receipt_id))

    receipt = db.receipts.find_one({'_id': ObjectId(receipt_id)})
    if not receipt:
        return jsonify({"error": "Receipt not found"}), 404
    items = receipt.get('items', [])
    return render_template('select_appetizers.html', items=items, receipt_id=receipt_id)


#allocate items -> people 

@app.route('/allocateitems/<receipt_id>', methods=['GET', 'POST'])
def allocateitems(receipt_id):
    if request.method == 'POST':
        # Clear previous allocations to avoid duplicates
        db.receipts.update_one({'_id': ObjectId(receipt_id)}, {'$unset': {'allocations': ''}})

        # Process form data and re-allocate items
        allocations = {key: request.form.getlist(key) for key in request.form.keys()}
        for name, items in allocations.items():
            if items:  # Ensure we don't push empty lists
                db.receipts.update_one(
                    {'_id': ObjectId(receipt_id)},
                    {'$push': {'allocations': {'name': name, 'items': items}}}
                )
        return redirect(url_for('enter_tip', receipt_id=receipt_id))

    # Fetch data to display form
    receipt = db.receipts.find_one({'_id': ObjectId(receipt_id)})
    if not receipt:
        return jsonify({"error": "Receipt not found"}), 404
    
    people = receipt.get('names', [])
    food_items = receipt.get('items', [])

    return render_template('allocateitems.html', people=people, food_items=food_items, receipt_id=receipt_id)

@app.route('/enter_tip/<receipt_id>', methods=['GET', 'POST'])
def enter_tip(receipt_id):
    if request.method == 'POST':
        return redirect(url_for('calculate_bill', receipt_id=receipt_id, tip_percentage=request.form['tip_percentage']))
    return render_template('enter_tip.html', receipt_id=receipt_id)




#calculate total, show total, update receipt in database 

@app.route('/calculate_bill/<receipt_id>', methods=['POST'])
def calculate_bill(receipt_id):
    try:
        logger.debug("Starting calculation of the bill.")
        
        # Retrieve and validate tip percentage
        tip_percentage_input = request.form.get('tip_percentage', '').strip()
        logger.debug(f"Received tip percentage: '{tip_percentage_input}'")
        
        # Validate that the tip percentage is a valid float
        try:
            tip_percentage = float(tip_percentage_input) / 100
        except ValueError:
            logger.error("Invalid tip percentage input.")
            return jsonify({"error": "Invalid tip percentage provided"}), 400

        # Fetching the receipt
        receipt = db.receipts.find_one({"_id": ObjectId(receipt_id)})
        if not receipt:
            logger.error("No receipt found.")
            return jsonify({"error": "Receipt not found"}), 404

        items = receipt.get('items', [])
        allocations = receipt.get('allocations', [])
        tax = float(receipt.get('tax', 0.00))
        subtotal = float(receipt.get('subtotal', 0.00))
        
        logger.debug(f"Subtotal and tax values: Subtotal={subtotal}, Tax={tax}")
        
        if not items or subtotal <= 0:
            logger.error("No items found or subtotal is zero or negative.")
            return jsonify({"error": "Invalid receipt data"}), 400

        payments = {name: 0 for name in receipt.get('names', [])}
        appetizer_total = sum(item.get('amount', 0.00) for item in items if item.get('is_appetizer', False))
        logger.debug(f"Total appetizer cost: {appetizer_total}")
        
        num_people = len(receipt.get('names', []))

        if num_people == 0:
            logger.error("Number of people is zero.")
            return jsonify({"error": "Number of people cannot be zero"}), 400

        appetizer_split = appetizer_total / num_people
        logger.debug(f"Appetizer cost per person: {appetizer_split}")

        for name in payments:
            payments[name] += appetizer_split
            logger.debug(f"Initial payment for {name}: {payments[name]}")

        # Calculating individual payments
        for allocation in allocations:
            for item_id in allocation['items']:
                item = next((item for item in items if str(item['_id']) == item_id), None)
                if item:
                    item_amount = item['amount']
                    payments[allocation['name']] += item_amount
                    logger.debug(f"Added {item_amount} to {allocation['name']}'s total from item {item['description']}")



        total_with_tax = subtotal + tax
        total_with_tip = total_with_tax * (1 + tip_percentage)
        logger.debug(f"Total with tax: {total_with_tax}, Total with tip: {total_with_tip}")

        # Distributing tax and tip across individuals
        for name, payment in payments.items():
            if subtotal > 0:
                person_share_before_tax = payment / subtotal
                payments[name] = payment + (total_with_tax + total_with_tip - subtotal) * person_share_before_tax
                logger.debug(f"Final payment for {name}: {payments[name]}")

        db.receipts.update_one({"_id": ObjectId(receipt_id)}, {'$set': {'payments': payments}})
        
        return render_template('results.html', payments=payments, receipt_id=receipt_id)
    except Exception as e:
        logger.error(f"Error in calculate_bill: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500



@app.route("/search_history")
def search_history():
    return render_template("search_history.html")

#route to show all the receipts history with functionality to search a keyword
@app.route("/history")
def history():
    keyword = request.args.get('search', None)
    
    query = {}
    if keyword:
        query = {"name": {"$regex": keyword, "$options": "i"}}
    
    items = db.receipts.find(query)
    items_list = list(items)

    return render_template("search_history.html", items=items_list)

@app.route('/test_mongodb')
def test_mongodb():
    try:
        info = db.command('serverStatus')
        return jsonify(success=True, message="Successfully connected to MongoDB", info=info), 200
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
@app.route('/test_ml_service')
def test_ml_service():
    response = requests.get('http://machine-learning-client:5002/test_connection')
    if response.status_code == 200:
        return jsonify(success=True, message="Connected to ML service", response=response.json()), 200
    else:
        return jsonify(success=False, message="Failed to connect to ML service"), 500
@app.route('/test_connection', methods=['GET'])
def test_connection():
    return jsonify(success=True, message="Machine Learning Client is reachable"), 200

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 10000))  # Default to 5000 if FLASK_PORT is not set

    app.run(debug=True, host='0.0.0.0')
