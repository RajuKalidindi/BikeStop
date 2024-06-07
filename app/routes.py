from flask import render_template, request, flash, redirect, url_for, get_flashed_messages
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
        query = "INSERT INTO customer (email, password, totalPaid, accountBalance, rentalStatus) VALUES (%s, %s, 0, 0, 0)"
        cursor.execute(query, (email, hashed_password))
        mysql.connection.commit()
        cursor.close()
        flash('Registration successful. Please login.')
        return redirect(url_for('login'))
    return render_template('registration.html')

@app.route('/user_home')
def user_home():
    cursor = mysql.connection.cursor()
    cursor.execute('''SELECT bikeID, locationID FROM bike WHERE locationID = 1''')
    data = cursor.fetchall()
    cursor.close()
    return render_template('user_home.html', data=data)

@app.route('/ride_history')
def ride_history():
    cursor = mysql.connection.cursor()
    cursor.execute('''SELECT bikeID, startTime, endTime, startLocation, endLocation, charged FROM customeractivity WHERE customerID = 4''')
    data = cursor.fetchall()
    cursor.close()
    return render_template('ride_history.html', data=data)

@app.route('/update_profile')
def update_profile():
    return render_template('update_profile.html')

@app.route('/operator_home')
def operator_home():
    cursor = mysql.connection.cursor()
    cursor.execute('''SELECT * FROM bike''')
    data = cursor.fetchall()
    cursor.execute('''SELECT * FROM bike WHERE bikeStatus = "broken"''')
    data1 = cursor.fetchall()
    cursor.close()
    return render_template('operator_home.html', data=data, data1=data1)

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
    generate_heatmap(locations, heatmap_image_path)
    cursor.execute("SELECT bikeID FROM customeractivity")
    bike_usage = [item[0] for item in cursor.fetchall()]
    bike_chart_image_path = os.path.join(dir_path, 'static/images/top_bikes_bar_chart.png')
    generate_bike_usage_chart(bike_usage, bike_chart_image_path)
    cursor.execute("SELECT customerID FROM customeractivity")
    customer_usage = [item[0] for item in cursor.fetchall()]
    customer_chart_image_path = os.path.join(dir_path, 'static/images/top_customers_pie_chart.png')
    generate_customer_usage_pie_chart(customer_usage, customer_chart_image_path)
    cursor.execute("SELECT startTime FROM customeractivity")
    start_times = [item[0] for item in cursor.fetchall()]
    cursor.close()
    line_chart_image_path = os.path.join(dir_path, 'static/images/rentals_by_hour_line_chart.png')
    generate_line_chart(start_times, line_chart_image_path)
    return render_template('manager_home.html')

