# ------------------------------------------------
# IMPORTS ----------------------------------------
# ------------------------------------------------
#####
# Python dist and 3rd party libraries
#####
import os, requests, json, string, datetime
from os.path import join, dirname
from flask import Flask, request, render_template, redirect, url_for
from flask.sessions import SessionInterface
from beaker.middleware import SessionMiddleware
#####
# Other python modules in WEA demo framework
#####
import application, watson, session, activate, over_activate, lookup

# ------------------------------------------------
# GLOBAL VARIABLES -------------------------------
# ------------------------------------------------
#####
# Session options
#####
session_opts = {
    'session.type': 'ext:memcached',
    'session.url': 'localhost:11211',
    'session.data_dir': './cache',
    'session.cookie_expires': 'true',
    'session.type': 'file',
    'session.auto': 'true'
}
#####
# in external modules
#####
CHAT_TEMPLATE = application.CHAT_TEMPLATE
QUESTION_INPUT = application.QUESTION_INPUT
CURSOR_INPUT = application.CURSOR_INPUT
SEARCH_TYPE_INPUT = application.SEARCH_TYPE_INPUT
# ------------------------------------------------
# CLASSES ----------------------------------------
# ------------------------------------------------
class BeakerSessionInterface(SessionInterface):
    def open_session(self, app, request):
        session = request.environ['beaker.session']
        return session

    def save_session(self, app, session, response):
        session.save()
# ------------------------------------------------
# FUNCTIONS --------------------------------------
# ------------------------------------------------
#####
# in external modules
#####
create_post = application.create_post
post_watson_response = application.post_watson_response
post_user_input = application.post_user_input
create_message = application.create_message
converse = application.converse
get_application_message = application.get_application_message
get_search_response = application.get_search_response
format_text = application.format_text
set_context_from_chat = application.set_context_from_chat
set_context_from_form = application.set_context_from_form
get_stt_token = watson.get_stt_token
get_tts_token = watson.get_tts_token
s = session.s
g = session.g
# ------------------------------------------------
# FLASK ------------------------------------------
# ------------------------------------------------
app = Flask(__name__)
app.register_blueprint(activate.activate)
app.register_blueprint(over_activate.over_activate)
app.register_blueprint(lookup.lookup)

@app.route('/')
def Index():
    global CHAT_TEMPLATE
#   Initialize SST & TTS tokens
    stt_token = get_stt_token()
    tts_token = get_tts_token()
    s('STT_TOKEN', stt_token)
    s('TTS_TOKEN', tts_token)
#   Initialize POSTS list
    s('POSTS',[])
#   Call conversation service/post response
    message = converse({})
    post_watson_response(format_text(message))
    return render_template(CHAT_TEMPLATE, posts=g('POSTS',[]), form='', stt_token=stt_token, tts_token=tts_token)

@app.route('/', methods=['POST'])
def Index_Post():
    global CHAT_TEMPLATE, QUESTION_INPUT
#   Capture value and display user question
    question = request.form[QUESTION_INPUT]
    
    post_user_input(question)
    #Get conversation response
    context = set_context_from_chat(question)
 
    while True:
        message = create_message(question, context)
        message = converse(message)
        application_message = get_application_message(message)
        if application_message['context'] == {}:
            break
        else:
            context = application_message['context']
            question = application_message['chat']
#   Display and render application_message
    output = application_message['chat']
    
    #post_watson_response(application_message['chat'])
    post_watson_response(output)
   
    return render_template(CHAT_TEMPLATE, posts=g('POSTS',[]), form=application_message['form'], context=message['context'], stt_token=g('STT_TOKEN', ''), tts_token=g('TTS_TOKEN', ''))
        
@app.route('/ivr', methods=['POST'])
def Index_Ivr():
#   Get data from post -- should be in the form of a conversation message
    data = json.loads(request.data)
    question = ''
    context = {}
    if 'input' in data:
        if 'text' in data['input']:
            question = data['input']['text']
            context = set_context_from_chat(question)
    if 'context' in data:
        for key in data['context']:
            context[key] = data['context'][key]
    while True:
        message = create_message(question, context)
        message = converse(message)
        application_message = get_application_message(message)
        if application_message['context'] == {}:
            break
        else:
            context = application_message['context']
            question = application_message['chat']
    return json.dumps(message, separators=(',',':'))
        
@app.route('/service', methods=['POST'])
def Service_Post():
#   Get data from post -- should be in the form of a conversation message
    message = json.loads(request.data)
    while True:
        next_message = {}
        if 'input' in message:
            next_message['input'] = message['input']
        if 'context' in message:
            next_message['context'] = message['context']
        message = converse(next_message)
        application_message = get_application_message(message)
        if application_message['context'] == {}:
            break
        else:
            message['input'] = json.loads('{"text": "' + application_message['chat'] + '"}')
            for key in application_message['context']:
                message['context'][key] = application_message['context'][key]
    return json.dumps(message, separators=(',',':'))
        
@app.route('/form', methods=['POST'])
def Form_Post():
    global CHAT_TEMPLATE
#   Capture values of form fields
    context = set_context_from_form(request.form)
#   Get conversation response
    message = create_message('', context)
    message = converse(message)
    application_message = get_application_message(message)
#   Display and render application_message
    post_watson_response(application_message['chat'])
    return render_template(CHAT_TEMPLATE, posts=g('POSTS',[]), form=application_message['form'], context=message['context'], stt_token=g('STT_TOKEN', ''), tts_token=g('TTS_TOKEN', ''))

@app.route('/page', methods=['POST'])
def Page_Post():
    global CHAT_TEMPLATE, CURSOR_INPUT, SEARCH_TYPE_INPUT
    form = ''
#   Set vars from hidden form fields
    action = request.form[CURSOR_INPUT]
    search_type = request.form[SEARCH_TYPE_INPUT]
    possible_actions = {'Accept': 0, 'Next': 1, 'Prev': -1, 'Explore': 0}
    shift = possible_actions[action]
    if shift != 0:
        application_response = get_search_response(search_type, shift)
    elif action == 'Accept':
        application_response = 'Thank you for helping to make Watson smarter! What else can I help you with?'
#   Display application_response
    post_watson_response(application_response)
    return render_template(CHAT_TEMPLATE, posts=g('POSTS',[]), form='', stt_token=g('STT_TOKEN', ''), tts_token=g('TTS_TOKEN', ''))

port = os.getenv('PORT', '5000')
if __name__ == "__main__":
    app.wsgi_app = SessionMiddleware(app.wsgi_app, session_opts)
    app.session_interface = BeakerSessionInterface()
#   app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
    app.run(host='0.0.0.0', port=int(port))
    #app.run(host='9.201.15.195', port=int(port))

