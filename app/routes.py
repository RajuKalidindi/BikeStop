from flask import Flask, render_template, request, flash, redirect, url_for, get_flashed_messages
from app import app
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

# app = Flask(__name__)
app.secret_key = '03SCJq89eWFjHZudC88z4HveX5ivc7A6'

#connecting to the database
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'bikestop'
app.config['MYSQL_UNIX_SOCKET'] = '/Applications/XAMPP/xamppfiles/var/mysql/mysql.sock'
 
mysql = MySQL(app)

#Creating routes for each of the webpages
@app.route('/')
def index():
    return render_template('index.html', title='Home')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        query = "SELECT * FROM customer WHERE email = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        print("result: ",result)

        if result is not None and check_password_hash(result[3], password):
            # The email and password are valid
            # You can log the user in and redirect them to their home page
            return redirect(url_for('user_home'))
        else:
            # The email or password is invalid
            flash('Invalid email or password')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/manager_login')
def manager_login():
    return render_template('manager_login.html')

@app.route('/operator_login')
def operator_login():
    return render_template('operator_login.html')

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':

        # Clear any existing flashed messages
        get_flashed_messages()

        email = request.form['email']
        password = request.form['password']
        password2 = request.form['password2']

        # Validate the form data
        if password != password2:
            flash('Passwords do not match')
            return redirect(url_for('registration'))

        # Check if the email already exists
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM customer WHERE email = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        if result:
            flash('Email already in use')
            return redirect(url_for('registration'))

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Insert the new user's data into the database
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
    cursor.execute('''SELECT bikeID,locationID FROM bike where locationID = 1''')
    data = cursor.fetchall()
    cursor.close()
    return render_template('user_home.html', data=data)

@app.route('/ride_history')
def ride_history():
    cursor = mysql.connection.cursor()
    cursor.execute('''SELECT bikeID,startTime,endTime,startLocation,endLocation,charged FROM customeractivity WHERE customerID = 4''')
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
    cursor.execute('''SELECT * FROM bike where bikeStatus = "broken"''')
    data1 = cursor.fetchall()
    cursor.close()
    return render_template('operator_home.html', data=data, data1=data1)

@app.route('/manager_home')
def manager_home():
    return render_template('manager_home.html')

@app.route('/test_db')
def test_db():
    try:
        conn = mysql.connection
        if conn.is_connected():
            return 'MySQL connection is working.'
    except Exception as e:
        return str(e)



