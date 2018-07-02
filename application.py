# ------------------------------------------------
# IMPORTS ----------------------------------------
# ------------------------------------------------
#####
# Python dist and 3rd party libraries
#####	
import os, requests, json, string, datetime, csv
#from flask import session
#####
# Other python modules in WEA demo framework
#####
import custom, watson, session, lookup
# ------------------------------------------------
# GLOBAL VARIABLES -------------------------------
# ------------------------------------------------
######
# Hardcoded env variable defaults for testing
#####
PERSONA_NAME = 'Partner'
PERSONA_IMAGE = ''
PERSONA_STYLE = 'Partner'
WATSON_IMAGE = ''
WATSON_STYLE = 'Watson'
CHAT_TEMPLATE = 'designer-index.html'
QUESTION_INPUT = 'response_input'
CURSOR_INPUT = 'cursor_input'
FORM_INPUT = 'form_input'
SEARCH_TYPE_INPUT = 'search-type'
SEARCH_VALUE_INPUT = 'search-values'
WKS_ANNOTATOR_MODEL_ID = None
#WKS_ANNOTATOR_MODEL_ID = 'ec91da29-60fd-4ba2-8d87-0a8e0be712ef'
#####
# Overwrites by env variables
#####
if 'PERSONA_NAME' in os.environ:
	PERSONA_NAME = os.environ['PERSONA_NAME']
if 'PERSONA_IMAGE' in os.environ:
	PERSONA_IMAGE = os.environ['PERSONA_IMAGE']
if 'PERSONA_STYLE' in os.environ:
	PERSONA_STYLE = os.environ['PERSONA_STYLE']
if 'WATSON_IMAGE' in os.environ:
	WATSON_IMAGE = os.environ['WATSON_IMAGE']
if 'WATSON_STYLE' in os.environ:
	WATSON_STYLE = os.environ['WATSON_STYLE']
if 'CHAT_TEMPLATE' in os.environ:
	CHAT_TEMPLATE = os.environ['CHAT_TEMPLATE']
if 'QUESTION_INPUT' in os.environ:
	QUESTION_INPUT = os.environ['QUESTION_INPUT']
if 'CURSOR_INPUT' in os.environ:
	CURSOR_INPUT = os.environ['CURSOR_INPUT']
if 'FORM_INPUT' in os.environ:
	FORM_INPUT = os.environ['FORM_INPUT']
if 'SEARCH_TYPE_INPUT' in os.environ:
	SEARCH_TYPE_INPUT = os.environ['SEARCH_TYPE_INPUT']
if 'SEARCH_VALUE_INPUT' in os.environ:
	SEARCH_VALUE_INPUT = os.environ['SEARCH_VALUE_INPUT']
if 'WKS_ANNOTATOR_MODEL_ID' in os.environ:
	WKS_ANNOTATOR_MODEL_ID = os.environ['WKS_ANNOTATOR_MODEL_ID']
####
# Tokens
#####
SEARCH_WITH_RANDR = '(--SEARCH_WITH_RANDR--)'
SEARCH_WITH_WEX = '(--SEARCH_WITH_WEX--)'
EVALUATE_PREDICTIVE_MODEL = '(--EVALUATE_PREDICTIVE_MODEL--)'
INVOKE_CUSTOM_SERVICE = '(--INVOKE_CUSTOM_SERVICE--)'
PRESENT_FORM = '(--FORM--)'
# ------------------------------------------------
# FUNCTIONS --------------------------------------
# ------------------------------------------------
#####
# in external modules
#####
populate_entity_from_randr_result = custom.populate_entity_from_randr_result
markup_randr_results = custom.markup_randr_results
populate_entity_from_wex_result = custom.populate_entity_from_wex_result
markup_wex_results = custom.markup_wex_results
set_context_from_predictive_model = custom.set_context_from_predictive_model
set_predictive_model_from_context = custom.set_predictive_model_from_context
invoke_custom_service = custom.invoke_custom_service
BMIX_converse = watson.BMIX_converse
BMIX_get_first_dialog_response_json = watson.BMIX_get_first_dialog_response_json
BMIX_get_next_dialog_response = watson.BMIX_get_next_dialog_response
BMIX_call_alchemy_api = watson.BMIX_call_alchemy_api
BMIX_evaluate_predictive_model = watson.BMIX_evaluate_predictive_model
BMIX_retrieve_and_rank = watson.BMIX_retrieve_and_rank
WEX_retrieve = watson.WEX_retrieve
#CHAT_TEMPLATE = lookup.CHAT_TEMPLATE
s = session.s
g = session.g
substitute_hash_values = lookup.substitute_hash_values
#####
# local
#####
# Chat presentation funcs ------------------------
def create_post(style, icon, text, datetime, name):
	post = {}
	post['style'] = style
	post['icon'] = icon
	post['text'] = text
	post['datetime'] = datetime
	post['name'] = name
	return post

def post_watson_response(response):
	global WATSON_STYLE, WATSON_IMAGE 
	now = datetime.datetime.now()
	post = create_post(WATSON_STYLE, WATSON_IMAGE, response, now.strftime('%Y-%m-%d %H:%M'), 'Watson')
	g('POSTS',[]).append(post)
	return post

def post_user_input(input):
	global PERSONA_STYLE, PERSONA_IMAGE, PERSONA_NAME
	now = datetime.datetime.now()
	post = create_post(PERSONA_STYLE, PERSONA_IMAGE, input, now.strftime('%Y-%m-%d %H:%M'), PERSONA_NAME)
	g('POSTS',[]).append(post)
	return post

# Watson helper funcs ----------------------------
def create_message(question, context):
	message = {}
	message['context'] = {}
	message['input'] = json.loads('{"text": "' + question + '"}')
	last_message = json.loads(g('MESSAGE', '{}'))
	if 'context' in last_message:
		message['context'] = last_message['context']
	for key in context:
		message['context'][key] = context[key]
	return message

def converse(message):
	message = BMIX_converse(message)
	s('MESSAGE', json.dumps(message))
	return message

# Context helper funcs ---------------------------
def set_context_from_chat(question):
	global WKS_ANNOTATOR_MODEL_ID
	context = {}
	if WKS_ANNOTATOR_MODEL_ID is not None:
		print('--Calling Alchemy')
		parameters = {}
		parameters['text'] = question.encode('ascii','ignore')
		parameters['extract'] = 'entities'
		parameters['disambiguate'] = '1'
		parameters['model'] = WKS_ANNOTATOR_MODEL_ID
		response = BMIX_call_alchemy_api('/text/TextGetRankedNamedEntities', parameters)
		print('--response')
		print(response)
		for entity in response['entities']:
			entity_type = entity['type']
			entity_text = entity['text'].encode('ascii','ignore')
			if entity_type not in context:
				context[entity_type] = entity_text
			elif type(context[entity_type]) is str:
				context[entity_type] = [context[entity_type]]
				context[entity_type].append(entity_text)
			else:
				context[entity_type].append(entity_text)
		print('--context')
		print(context)
	return context

def set_context_from_form(form):
	context = {}
	for field in form:
		context[field] = form[field]
	return context

# Search helper funcs ----------------------------
def get_search_response(search_type, shift):
	search_response = ''
	if search_type == "RANDR":
		s('RANDR_CURSOR', shift_cursor(g('RANDR_SEARCH_RESULTS', []), g('RANDR_CURSOR', 0), shift))
		search_response = markup_randr_results(g('RANDR_SEARCH_RESULTS', []), g('RANDR_CURSOR', 0))
	elif search_type == "WEX":
		s('WEX_CURSOR', shift_cursor(g('WEX_SEARCH_RESULTS', []), g('WEX_CURSOR', 0), shift))
		search_response = markup_wex_results(g('WEX_SEARCH_RESULTS', []), g('WEX_CURSOR', 0))
	return search_response

def search_randr(question):
	#global RANDR_SEARCH_ARGS
	randr_search_results = []
	randr_cursor = 0
	application_response = ''
	docs = BMIX_retrieve_and_rank(question)
	i = 0
	for doc in docs:
		i += 1
		entity = populate_entity_from_randr_result(doc)
		randr_search_results.append(entity)
	application_response = markup_randr_results(randr_search_results, randr_cursor)
	s('RANDR_SEARCH_RESULTS', randr_search_results)
	s('RANDR_CURSOR', randr_cursor)
	return application_response

def search_wex(question):
	wex_search_results = []
	wex_cursor = 0
	application_response = ''
	docs = WEX_retrieve(question)
	i = 0
	for doc in docs:
		i += 1
		entity = populate_entity_from_wex_result(doc)
		wex_search_results.append(entity)
	application_response = markup_wex_results(wex_search_results, wex_cursor)
	s('WEX_SEARCH_RESULTS', wex_search_results)
	s('WEX_CURSOR', wex_cursor)
	return application_response

def shift_cursor(search_results, cursor, shift):
	cursor = cursor + shift
	if cursor < 0:
		cursor = max(len(search_results)-1,0)
	elif cursor >= len(search_results):
		cursor = 0
	return cursor
	
def extract_search_arg(message):
	search_arg = ''
	if 'input' in message:
		input = message['input']
		if 'text' in input:
			search_arg = input['text']
	return search_arg

def extract_context(message):
	context = {}
	if 'context' in message:
		context = message['context']
	return context

# Predictive Analytics helper funcs --------------
def extract_predictive_model(message):
	model = {}
	if 'context' in message:
		context = message['context']
		if 'predictive_model' in context:
			model = context['predictive_model']
		else:
			model = set_predictive_model_from_context(context)
	return model

# Application funcs ------------------------------
def format_text(message):
	formatted_text = 'The chat-bot is not currently available. Try again?'
	if 'output' in message:
		output = message['output']
		if 'text' in output:
			formatted_text = ''
			text = output['text']
			for dialog_response_line in text:
				if str(dialog_response_line) != '':
					if len(formatted_text) > 0:
						formatted_text = formatted_text + ' ' + dialog_response_line
					else:
						formatted_text = dialog_response_line
	return formatted_text

def get_form(text):
	global PRESENT_FORM
	form = ''
	if PRESENT_FORM in text:
		responses = text.split(PRESENT_FORM)
		form = responses[1]
	return form

def get_chat(text):
	global PRESENT_FORM
	chat = text
	if PRESENT_FORM in text:
		responses = text.split(PRESENT_FORM)
		chat = responses[0]
	chat = substitute_hash_values(chat)
	return chat
	
def get_application_message(message):
	formatted_text = format_text(message)
	chat = get_chat(formatted_text)
	form = get_form(formatted_text)
	#application_message
	application_message = {'chat': chat, 'form': form, 'context': {}}
	#substitute hash map values
	#for key in HASH_VALUES:
		#value = HASH_VALUES[key]
		#application_message['chat'] = application_message['chat'].replace(key, value)
	#randr search requested
	if (application_message['chat'].startswith(SEARCH_WITH_RANDR)):
		search_arg = extract_search_arg(message)
		application_message['chat'] = search_randr(search_arg)
	#wex search requested
	if (application_message['chat'].startswith(SEARCH_WITH_WEX)):
		search_arg = extract_search_arg(message)
		application_message['chat'] = search_wex(search_arg)
	#predictive model evaluated
	if (application_message['chat'].startswith(EVALUATE_PREDICTIVE_MODEL)):
		application_message['chat'] = application_message['chat'].replace(EVALUATE_PREDICTIVE_MODEL, '')
		model = extract_predictive_model(message)
		entity = BMIX_evaluate_predictive_model(model)
		application_message['context'] = set_context_from_predictive_model(entity)
	#custom service invoked
	if (application_message['chat'].startswith(INVOKE_CUSTOM_SERVICE)):
		application_message['chat'] = application_message['chat'].replace(INVOKE_CUSTOM_SERVICE, '')
		context = extract_context(message)
		application_message['context'] = invoke_custom_service(context, application_message['chat'])
	return application_message
