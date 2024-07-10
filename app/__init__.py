from flask import Flask
from flask_mysqldb import MySQL
from dotenv import load_dotenv
import os
import nltk
nltk.download('stopwords')
nltk.download('punkt')

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Configuration
app.config.from_object('app.config.Config')

mysql = MySQL(app)

from app import routes
