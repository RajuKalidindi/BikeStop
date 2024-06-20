from flask import render_template, request, flash, redirect, url_for, get_flashed_messages, session, jsonify
from app import app, mysql
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils import (
    generate_wordcloud, save_wordcloud, generate_bar_chart, generate_heatmap, 
    generate_bike_usage_chart, generate_customer_usage_pie_chart, generate_line_chart
)
import os

@app.route('/')
def index():
    return render_template('index.html', title='Home')

@app.route('/login', methods=['GET', 'POST'])
def login():
    get_flashed_messages()
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM customer WHERE email = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        if result is not None and check_password_hash(result[3], password):
            session['customerID'] = result[0]
            return redirect(url_for('user_home'))
        else:
            flash('Invalid email or password')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/manager_login', methods=['GET', 'POST'])
def manager_login():
    if request.method == 'POST':
        get_flashed_messages()
        manager_password = request.form['manager_password']
        secret_key = 'manager_password'

        if manager_password == secret_key:
            return redirect(url_for('manager_home'))
        else:
            flash('Invalid password')
            return redirect(url_for('manager_login'))
    return render_template('manager_login.html')

@app.route('/operator_login', methods=['GET', 'POST'])
def operator_login():
    if request.method == 'POST':
        get_flashed_messages()
        operator_password = request.form['operator_password']
        secret_key = 'operator_password'

        if operator_password == secret_key:
            return redirect(url_for('operator_home'))
        else:
            flash('Invalid password')
            return redirect(url_for('operator_login'))
    return render_template('operator_login.html')

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        get_flashed_messages()
        first_name = request.form['firstName']
        last_name = request.form['lastName']
        email = request.form['email']
        password = request.form['password']
        password2 = request.form['password2']
        if password != password2:
            flash('Passwords do not match')
            return redirect(url_for('registration'))
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM customer WHERE email = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        if result:
            flash('Email already in use')
            return redirect(url_for('registration'))
        hashed_password = generate_password_hash(password)
        query = "INSERT INTO customer (email, password, firstName, lastName, totalPaid, accountBalance, rentalStatus) VALUES (%s, %s, %s, %s, 0, 0, 0)"
        cursor.execute(query, (email, hashed_password, first_name, last_name))
        mysql.connection.commit()
        cursor.close()
        flash('Registration successful. Please login.')
        return redirect(url_for('login'))
    return render_template('registration.html')

@app.route('/user_home',  methods=['GET', 'POST'])
def user_home():
    cursor = mysql.connection.cursor()
    customer_id = session['customerID']
    cursor.execute("SELECT firstName, accountBalance FROM customer WHERE customerID = %s", (customer_id,))
    user = cursor.fetchone()
    cursor.execute("SELECT locationName FROM location")
    postcodes = [item[0] for item in cursor.fetchall()]
    selected_location = 'University of Glasgow'  # Default locationName
    if request.method == 'POST':
        selected_location = request.form['location']
    cursor.execute("SELECT locationID FROM location WHERE locationName = %s", (selected_location,))
    location_id = cursor.fetchone()[0]
    cursor.execute("""
    SELECT bike.bikeID, bike.bikeStatus, location.locationName 
    FROM bike 
    INNER JOIN location ON bike.locationID = location.locationID 
    WHERE bike.locationID = %s AND bike.rentalStatus = 0
    """, (location_id,))
    bikeData = cursor.fetchall()
    cursor.close()
    return render_template('user_home.html', postcodes=postcodes, bikeData=bikeData, user=user[0], accountBalance=user[1])

@app.route('/start-ride', methods=['POST'])
def start_ride():
    bike_id = request.json['bikeId']
    session['bikeID'] = bike_id
    customer_id = session['customerID']
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT locationID FROM bike WHERE bikeID = %s", (bike_id,))
    start_location_id = cursor.fetchone()[0]
    cursor.execute("UPDATE customer SET rentalStatus = 1 WHERE customerID = %s", (customer_id,))
    cursor.execute("UPDATE bike SET rentalStatus = 1 WHERE bikeID = %s", (bike_id,))
    cursor.execute("INSERT INTO customeractivity (customerID, bikeID, startTime, startLocation, paid) VALUES (%s, %s, NOW(), %s, 0)", (customer_id, bike_id, start_location_id))
    print("customer activity added")
    mysql.connection.commit()
    cursor.close()
    return jsonify({'status': 'success'})

@app.route('/end-ride', methods=['POST'])
def end_ride():
    endLocation = request.json['endLocation']
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT locationID FROM location WHERE locationName = %s", (endLocation,))
    end_location_id = cursor.fetchone()[0]
    bike_id = request.json['bikeId']
    print("bike id:",bike_id)
    customer_id = session['customerID']
    print("customer id:",customer_id)
    cursor.execute("UPDATE bike SET rentalStatus = 0, locationID = %s WHERE bikeID = %s", (end_location_id, bike_id))
    cursor.execute("UPDATE customer SET rentalStatus = 0 WHERE customerID = %s", (customer_id,))
    cursor.execute("""
    UPDATE customeractivity 
    SET endTime = NOW(), 
        endLocation = %s, 
        charged = GREATEST(TIMESTAMPDIFF(MINUTE, startTime, NOW()) / 60.0 * 10, 1) 
    WHERE customerID = %s AND bikeID = %s AND endTime IS NULL""", (end_location_id, customer_id, bike_id))
    cursor.execute("SELECT charged FROM customeractivity WHERE customerID = %s AND bikeID = %s AND endTime IS NOT NULL ORDER BY endTime DESC LIMIT 1", (customer_id, bike_id))
    charged = cursor.fetchone()[0]
    cursor.execute("SELECT accountBalance FROM customer WHERE customerID = %s", (customer_id,))
    account_balance = cursor.fetchone()[0]
    if account_balance >= charged:
        cursor.execute("UPDATE customer SET accountBalance = accountBalance - %s WHERE customerID = %s", (charged, customer_id))
        cursor.execute("UPDATE customeractivity SET paid = 1 WHERE customerID = %s AND bikeID = %s AND endTime IS NOT NULL ORDER BY endTime DESC LIMIT 1", (customer_id, bike_id))
        cursor.execute("UPDATE customer SET totalPaid = totalPaid + %s WHERE customerID = %s", (charged, customer_id))
    mysql.connection.commit()
    cursor.close()
    return jsonify({'status': 'success'})

@app.route('/save_review', methods=['POST'])
def save_review():
    rating = request.form['rating']
    comment = request.form['comment']
    customer_id = session['customerID']
    bike_id = session['bikeID']
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO reviews (customerID, bikeID, rating, comments, reviewTime) VALUES (%s, %s, %s, %s, NOW())", (customer_id, bike_id, rating, comment))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('user_home'))

@app.route('/get-rental-status', methods=['GET'])
def get_rental_status():
    customer_id = session['customerID'] 
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT rentalStatus FROM customer WHERE customerID = %s", (customer_id,))
    rental_status = cursor.fetchone()[0]
    cursor.close()
    return jsonify({'rentalStatus': rental_status})

@app.route('/ride_history')
def ride_history():
    cursor = mysql.connection.cursor()
    customer_id = session['customerID']
    cursor.execute("SELECT firstName FROM customer WHERE customerID = %s", (customer_id,))
    user = cursor.fetchone()
    cursor.execute('''
    SELECT 
        ca.bikeID, 
        ca.startTime, 
        ca.endTime, 
        startLoc.locationName AS startLocationName, 
        endLoc.locationName AS endLocationName, 
        ca.charged 
    FROM customeractivity ca
    LEFT JOIN location startLoc ON ca.startLocation = startLoc.locationID
    LEFT JOIN location endLoc ON ca.endLocation = endLoc.locationID
    WHERE ca.customerID = %s 
    ORDER BY ca.startTime DESC
    ''', (session['customerID'],))
    data = cursor.fetchall()
    cursor.close()
    return render_template('ride_history.html', data=data, user=user[0])

@app.route('/update_profile')
def update_profile():
    cursor = mysql.connection.cursor()
    customer_id = session['customerID']
    cursor.execute("SELECT firstName FROM customer WHERE customerID = %s", (customer_id,))
    user = cursor.fetchone()
    return render_template('update_profile.html', user=user[0])

@app.route('/update_password', methods=['POST'])
def update_password():
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    customer_id = session['customerID']
    if new_password == confirm_password:
        hashed_password = generate_password_hash(new_password)
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE customer SET password = %s WHERE customerID = %s", (hashed_password, customer_id))
        mysql.connection.commit()
        cursor.close()
        flash('Password updated successfully', 'success')
        return redirect(url_for('update_profile'))
    else:
        flash('Passwords do not match', 'danger')
        return redirect(url_for('update_profile'))
    
@app.route('/update_card', methods=['POST'])
def update_card():
    new_card_number = request.form['card_number']
    expiry_date = request.form['expiry_date']
    cvv = request.form['cvv']
    customer_id = session['customerID']
    print(new_card_number, expiry_date, cvv, customer_id)
    if new_card_number and expiry_date and cvv:
        hashed_card_number = generate_password_hash(new_card_number)
        hashed_expiry_date = generate_password_hash(expiry_date)
        hashed_cvv = generate_password_hash(cvv)
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE customer SET cardNumber = %s, expiryDate = %s, cvv = %s WHERE customerID = %s", (hashed_card_number, hashed_expiry_date, hashed_cvv, customer_id))
        mysql.connection.commit()
        cursor.close()
        flash('Card details updated successfully', 'success')
        return redirect(url_for('update_profile'))
    else:
        flash('Card update failed. Please try again.', 'danger')
        return redirect(url_for('update_profile'))
    
@app.route('/update_balance', methods=['POST'])
def update_balance():
    amount = request.form['topup_amount']
    customer_id = session['customerID']
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT cardNumber, expiryDate, cvv FROM customer WHERE customerID = %s", (customer_id,))
    card_details = cursor.fetchone()
    # Check if the hashed card details exist
    if card_details and all(card_details):
        cursor.execute("UPDATE customer SET accountBalance = accountBalance + %s WHERE customerID = %s", (amount, customer_id))
        mysql.connection.commit()
        flash('Balance updated successfully' , 'success')
    else:
        flash('Add your card details to top-up account balance', 'danger')
        return redirect(url_for('update_profile'))

    cursor.close()
    return redirect(url_for('user_home'))

@app.route('/operator_home')
def operator_home():
    cursor = mysql.connection.cursor()
    cursor.execute('''
    SELECT 
        b.bikeID, 
        b.bikeStatus, 
        l.locationName,
        CASE 
            WHEN b.rentalStatus = 0 THEN 'No'
            WHEN b.rentalStatus = 1 THEN 'Yes'
            ELSE 'Unknown'
        END as rentalStatus
    FROM bike b
    LEFT JOIN location l ON b.locationID = l.locationID
    ''')
    bikeData = cursor.fetchall()
    cursor.execute('''
        SELECT 
            b.bikeID, 
            b.bikeStatus, 
            l.locationName 
        FROM bike b
        LEFT JOIN location l ON b.locationID = l.locationID
        WHERE b.bikeStatus = "broken"
    ''')
    brokenData = cursor.fetchall()
    cursor.close()
    return render_template('operator_home.html', bikeData=bikeData, brokenData=brokenData)

@app.route('/update_bike_location', methods=['POST'])
def update_bike_location():
    bike_no = request.form['bike_no']
    new_location = request.form['new_location']
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT locationID FROM location WHERE locationName = %s", (new_location,))
    location_id = cursor.fetchone()[0]
    cursor.execute("UPDATE bike SET locationID = %s WHERE bikeID = %s", (location_id, bike_no,))
    cursor.execute("INSERT INTO operatoractivity (bikeID, actionName, action_time) VALUES (%s, 'move', NOW())", (bike_no,))
    mysql.connection.commit()
    cursor.close()
    flash("Bike location updated successfully")
    return redirect(url_for('operator_home'))

@app.route('/update_bike_status', methods=['POST'])
def update_bike_status():
    bike_no = request.form['bike_no']
    print(bike_no)
    new_status = request.form['new_status']
    print(new_status)
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE bike SET bikeStatus = %s WHERE bikeID = %s", (new_status, bike_no,))
    cursor.execute("INSERT INTO operatoractivity (bikeID, actionName, action_time) VALUES (%s, 'repair', NOW())", (bike_no,))
    mysql.connection.commit()
    cursor.close()
    flash("Bike status updated successfully")
    return redirect(url_for('operator_home'))

@app.route('/manager_home')
def manager_home():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT comments FROM reviews")
    comments = ' '.join([item[0] for item in cursor.fetchall()])
    wordcloud = generate_wordcloud(comments)
    dir_path = os.path.dirname(os.path.realpath(__file__))
    wordcloud_image_path = os.path.join(dir_path, 'static/images/wordcloud.png')
    save_wordcloud(wordcloud, wordcloud_image_path)
    cursor.execute("SELECT rating FROM reviews")
    ratings = [item[0] for item in cursor.fetchall()]
    bar_chart_image_path = os.path.join(dir_path, 'static/images/rating_bar_chart.png')
    generate_bar_chart(ratings, bar_chart_image_path)
    cursor.execute("SELECT startLocation, endLocation FROM customeractivity")
    locations = cursor.fetchall()
    heatmap_image_path = os.path.join(dir_path, 'static/images/routes_heatmap.png')
    cursor.execute("SELECT locationID, locationName FROM location")
    location_name_data = cursor.fetchall()
    location_names = {id: name for id, name in location_name_data}
    generate_heatmap(locations, location_names, heatmap_image_path)
    cursor.execute("SELECT bikeID FROM customeractivity")
    bike_usage = [item[0] for item in cursor.fetchall()]
    bike_chart_image_path = os.path.join(dir_path, 'static/images/top_bikes_bar_chart.png')
    generate_bike_usage_chart(bike_usage, bike_chart_image_path)
    cursor.execute("SELECT customerID FROM customeractivity")
    customer_usage = [item[0] for item in cursor.fetchall()]
    customer_chart_image_path = os.path.join(dir_path, 'static/images/top_customers_pie_chart.png')
    cursor.execute("SELECT customerID, CONCAT(firstName, ' ', lastName) as customerName FROM customer")
    customers = cursor.fetchall()
    customer_names = {id: name for id, name in customers}
    generate_customer_usage_pie_chart(customer_usage, customer_names, customer_chart_image_path)
    cursor.execute("SELECT startTime FROM customeractivity")
    start_times = [item[0] for item in cursor.fetchall()]
    cursor.close()
    line_chart_image_path = os.path.join(dir_path, 'static/images/rentals_by_hour_line_chart.png')
    generate_line_chart(start_times, line_chart_image_path)
    return render_template('manager_home.html')

