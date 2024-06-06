# BikeStop

Flask GUI Installation

Go into the GUI directory and run the following commands in anaconda prompt for setting up flask

pip install -r requirements.txt – Installs all the required packages

set FLASK_APP=bikestop.py
For Linux system when running on terminal use "export" instead of "set" in the command above

Run the apache server and mysql server on xampp control panel as the database is hosted there. Then execute the below command

flask run

If the program successfully executes open this link in the browser for login page
http://127.0.0.1:5000/login
