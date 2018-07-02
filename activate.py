# Imports
import os, requests, json, string, datetime
from flask import Blueprint, render_template, abort, request, redirect, url_for
import application, watson, session

# Global variables
REQUEST_A_CODE = 'Request a code'
CHAT_TEMPLATE = application.CHAT_TEMPLATE

# In external modules
set_context_from_form = application.set_context_from_form
create_message = application.create_message
converse = application.converse
get_application_message = application.get_application_message
post_watson_response = application.post_watson_response
CIRON_get_asset_activation_code = watson.CIRON_get_asset_activation_code
s = session.s
g = session.g

# Flask
activate = Blueprint('activate', __name__, static_folder='static', template_folder='templates')

@activate.route('/activate', methods=['POST'])
def Index():
	global CHAT_TEMPLATE, REQUEST_A_CODE
# Capture values of form fields
	context = set_context_from_form(request.form)
	message = create_message('', context)
# Determine user action
	if request.form['response_input'] == REQUEST_A_CODE:
		castiron_response = CIRON_get_asset_activation_code(json.dumps(message['context'], separators=(',',':')))
		message['context']['castiron_response'] = castiron_response
	message = converse(message)
	application_message = get_application_message(message)
# Display and render application_message
	post_watson_response(application_message['chat'])
	return render_template(CHAT_TEMPLATE, posts=g('POSTS',[]), form=application_message['form'], context=message['context'])