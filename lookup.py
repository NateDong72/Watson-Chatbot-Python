# Imports
import os, requests, json, string, datetime, csv
from flask import Blueprint, render_template, abort, request, redirect, url_for
import session

# Global variables
HASH_VALUES = {}

# In external modules
s = session.s
g = session.g

#local
def load_hash_values(app):
	hash_values = {}
	with app.open_resource('hash.csv') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			hash_values[row['key']] = row['value']
	return hash_values

def substitute_hash_values(chat):
	global HASH_VALUES
	tokens = chat.split()
	for token in tokens:
		if token in HASH_VALUES:
			chat = chat.replace(token, HASH_VALUES[token])
	return chat

# Flask
lookup = Blueprint('lookup', __name__, static_folder='static', template_folder='templates')
HASH_VALUES = load_hash_values(lookup)

@lookup.route('/lookup', methods=['POST'])
def Index():
	return "Lookup..."