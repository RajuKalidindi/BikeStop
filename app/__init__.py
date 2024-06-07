from flask import Flask
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = '03SCJq89eWFjHZudC88z4HveX5ivc7A6'

# Configuration
app.config.from_object('app.config.Config')

mysql = MySQL(app)

from app import routes
