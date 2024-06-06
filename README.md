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

File Structure

├── **pycache**
├── LICENSE
├── bikestop.py
├── README.md
├── requirements.txt
├── app
│ ├── **pycache**
│ ├── static
│ │ ├── css
│ │ │ ├── login.css
│ │ │ ├── registration.css
│ │ │ ├── update_profile.css
│ │ │ ├── user_home.css
│ │ ├── images
│ │ │ ├── 1.png
│ │ │ ├── 2.png
│ │ │ ├── 3.png
│ │ │ ├── 4.png
│ │ │ ├── 5.png
│ │ │ ├── 6.png
│ │ │ ├── login.jpg
│ │ │ ├── profile.jfif
│ ├── templates
│ │ ├── base.html
│ │ ├── index.html
│ │ ├── login.html
│ │ ├── manager_home.html
│ │ ├── manager_login.html
│ │ ├── operator_home.html
│ │ ├── operator_login.html
│ │ ├── registration.html
│ │ ├── ride_history.py
│ │ ├── update_profile.html
│ │ ├── user_home.html
│ ├── **init**.py
│ ├── routes.py
