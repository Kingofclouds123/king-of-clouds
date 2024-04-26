from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_pymongo import PyMongo
from bson import ObjectId
from gridfs import GridFS
from io import BytesIO
from flask_cors import CORS
import razorpay

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

app.config["MONGO_URI"] = "mongodb+srv://poras:Blackhat2000@cluster0.xpsu7jv.mongodb.net/kingsofcloud?retryWrites=true&w=majority&appName=Cluster0"
mongo = PyMongo(app)
fs = GridFS(mongo.db)

client = razorpay.Client(auth=("rzp_test_zMgntNJdTTMAVw", "S0lRGW3LrlTllY6uDFjUtAf2"))

@app.route("/")
def hello_world():
    return render_template('index.html')

@app.route("/upload", methods=["POST"])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        file_data = file.read()
        filename = file.filename
        file_id = fs.put(file_data, filename=filename)
        return jsonify({"message": "File uploaded successfully", "file_id": str(file_id)}), 200

@app.route("/get/<file_id>")
def get_image(file_id):
    try:
        file_id = ObjectId(file_id)
        file_data = fs.get(file_id)
        response = BytesIO(file_data.read())
        response.seek(0)
        return send_file(response, mimetype='image/jpeg')
    except Exception as e:
        return jsonify({"error": str(e)}), 400

import base64

@app.route("/get_all")
def get_all_images():
    try:
        images = []
        for file in fs.find():
            image_data = file.read()
            image_id = str(file._id)
            # Encode image data to base64
            image_data_base64 = base64.b64encode(image_data).decode('utf-8')
            images.append({"_id": image_id, "data": image_data_base64})
        return jsonify({"images": images})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/delete/<file_id>", methods=["DELETE"])
def delete_image(file_id):
    try:
        # Convert file_id to ObjectId
        file_id = ObjectId(file_id)
        
        # Delete the image from GridFS using the file_id
        fs.delete(file_id)
        
        # Return a success message
        return jsonify({"message": "Image deleted successfully"}), 200
    except Exception as e:
        # If an error occurs, return an error message
        return jsonify({"error": str(e)}), 400

@app.route('/pay', methods=['GET'])
def pay():
    order_id = request.args.get('order_id')
    name = request.args.get('name')
    email = request.args.get('email')
    phone = request.args.get('phone')
    person = request.args.get('person')
    reservation_date = request.args.get('reservation_date')
    reservation_time = request.args.get('reservation_time')
    amount = request.args.get('amount')
    currency = request.args.get('currency')

    # Bundle form data into a variable named pdata
    pdata = {
        'order_id': order_id,
        'name': name,
        'email': email,
        'phone': phone,
        'person': person,
        'reservation_date': reservation_date,
        'reservation_time': reservation_time,
        'amount': amount,
        'currency': currency
    }

    # Render the payment page with the form data bundled in pdata
    return render_template('payment.html', pdata=pdata)


@app.route('/success', methods=["POST"])
def success():
    pid=request.form.get("razorpay_payment_id")
    ordid=request.form.get("razorpay_order_id")
    sign=request.form.get("razorpay_signature")
    print(f"The payment id : {pid}, order id : {ordid} and signature : {sign}")
    params={
    'razorpay_order_id': ordid,
    'razorpay_payment_id': pid,
    'razorpay_signature': sign
    }
    final=client.utility.verify_payment_signature(params)
    if final == True:
        return redirect("/", code=301)
    return "Something Went Wrong Please Try Again"


@app.route('/create_order', methods=['POST'])
def create_order():
    try:
        # Get data from the form
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        person = int(request.form['person'])  # Number of persons
        reservation_date = request.form['reservation-date']
        reservation_time = request.form['reservation-time']
        amount = 2500 * person  # Amount per person

        # Create order
        order = client.order.create({'amount': amount * 100, 'currency': 'INR'})

        # Redirect to Razorpay payment gateway with order ID and form data as query parameters
        return redirect(url_for('pay', order_id=order['id'], 
                                name=name, email=email, phone=phone,
                                person=person, reservation_date=reservation_date,
                                reservation_time=reservation_time, amount=amount, currency='INR'))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    
@app.route('/verify_payment', methods=['POST'])
def verify_payment():
    try:
        # Get data from Razorpay webhook
        data = request.get_json()
        payment_id = data['payload']['payment']['entity']['id']
        
        # Fetch payment details
        payment = razorpay_client.payment.fetch(payment_id)
        
        # Verify payment amount and status
        if payment['amount'] == data['payload']['payment']['entity']['amount'] and payment['status'] == 'captured':
            # Payment is valid
            return jsonify({'message': 'Payment successful'}), 200
        else:
            # Payment is invalid
            return jsonify({'error': 'Payment verification failed'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/payment_success', methods=['POST'])
def payment_success():
    try:
        # Parse data from the request
        data = request.json
        order_id = data.get('order_id')
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        amount = data.get('amount')
        person = data.get('person')
        reservation_date = data.get('reservation_date')
        reservation_time = data.get('reservation_time')

        # Access the MongoDB collection
        payments_collection = mongo.db.payments

        # Create a new payment document
        payment_data = {
            'order_id': order_id,
            'name': name,
            'email': email,
            'phone': phone,
            'amount': amount,
            'currency': currency
        }

        # Insert the payment document into the payments collection
        result = payments_collection.insert_one(payment_data)

        # Check if the insertion was successful
        if result.inserted_id:
            return jsonify({'message': 'Payment data saved successfully'}), 200
        else:
            return jsonify({'error': 'Failed to save payment data'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 400

    
if __name__ == '__main__':
    app.run(debug=True)
