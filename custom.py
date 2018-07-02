# ------------------------------------------------
# IMPORTS ----------------------------------------
# ------------------------------------------------
#####
# Python dist and 3rd party libraries
#####
import os, requests, json, string, datetime, csv
from pprint import pprint
import xmltodict
# ------------------------------------------------
# FUNCTIONS --------------------------------------
# ------------------------------------------------
#####
# local
#####
# Search helper funcs ----------------------------
def populate_entity_from_randr_result(doc):
	entity = {}
	entity['id'] = doc['id']
	entity['body'] = doc['body'][0]
	entity['title'] = doc['title'][0]
	entity['author'] = doc['author'][0]
	entity['RunBook_URL'] = doc['RunBook_URL'][0]
	return entity

def markup_randr_result(entity):
	return ('<p><b>' + entity['title'] + '</b><br><u>Body:</u> ' + entity['body'] + '<br><u>Runbook URL:</u> ' + entity['RunBook_URL'] + '<br><u>Document id:</u> ' + entity['id']+ '</p>')

def markup_randr_results(search_results, cursor):
	application_response = "I'm unable to find what you're looking for. Can you rephrase the question or ask something else?"
	if (len(search_results) > 0):
		entity = search_results[cursor]
		application_response = "I've retrieved <b>" + str(len(search_results)) + " documents</b> that may be of interest. You're viewing document number <b>#" + str(cursor + 1) + "</b>"
		application_response = application_response + markup_randr_result(entity)
		application_response = application_response + '<form action="/page" method="POST"><input type="submit" name="cursor_input" value="Next"/> <input type="submit" name="cursor_input" value="Prev"/> <input type="submit" type="submit" name="cursor_input" value="Accept"/> <input type="hidden" name="search-type" value="RANDR"></form>'
	return application_response

def populate_entity_from_wex_result(doc):
	entity = {}
	entity['Url'] = doc['@url']
	entity['FileType'] = doc['@filetypes']
	entity['Snippet'] = ""
	entity['FileName'] = ""
	contents = doc['content']
	for content in contents:
		name = content['@name']
		if name == 'snippet':
			entity['Snippet'] = content['#text']
		if name == 'filename':
			entity['FileName'] = content['#text']
	return entity

def markup_wex_results(search_results, cursor):
	application_response = "I'm unable to find what you're looking for. Can you rephrase the question or ask something else?"
	if (len(search_results) > 0):
		entity = search_results[cursor]
		application_response = "I've found the answer to your question in <b>" + str(len(search_results)) + " documents</b> with the most probable answers shown first. You're viewing answer <b>#" + str(cursor + 1) + "</b>"
		url = entity['Url']
		application_response = application_response + '<p style="font-size: small;"><i>' + entity['Snippet'] + '</i> <a href="' + url + '" style="font-size: small;" target="_blank">View document</a></p>'
		application_response = application_response + '<form action="/page" method="POST"><input type="submit" name="cursor_input" value="Next"/> <input type="submit" name="cursor_input" value="Prev"/> <input type="submit" type="submit" name="cursor_input" value="Accept"/> <input type="hidden" name="search-type" value="WEX"></form>'
	return application_response

# Predictive Analytics helper funcs --------------
def set_predictive_model_from_context(context):
	model = {}
#	implement code to build predictive model from context
	return model

def set_context_from_predictive_model(entity):
	context = {}
	if type(entity) is list:
		campaign = entity[0]
		attr_names = campaign['header']
		attr_values = campaign['data'][0]
		i = 0
		for attr_name in attr_names:
			context[attr_name.replace('$', '').replace(' ', '_').replace('-', '_')] = attr_values[i]
			i += 1
	return context

# Custom service func ----------------------------
def invoke_custom_service(message_context, custom_service_label):
	application_context = {}
	return application_context