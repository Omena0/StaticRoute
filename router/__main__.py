import os

import flask

from .load import load_data_stores, load_routes_json

# Load routes
routes = load_routes_json()

BASEDIR = "data_stores"
os.makedirs(BASEDIR, exist_ok=True)

# Define app
app = flask.Flask(__name__)
app.secret_key = "1234"

load_data_stores(app, BASEDIR, routes)

app.run(debug=True)
