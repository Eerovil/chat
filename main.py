#! /usr/bin/python
# -*- encoding: utf-8 -*-

import datetime
import re
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from sqlitedict import SqliteDict

app = Flask(__name__, template_folder='templates', static_url_path='/static/', static_folder='static')
SqliteDict('main.db', tablename="main", autocommit=True)

app.config['SECRET_KEY'] = 'eero'
socketio = SocketIO(app)

@app.route('/')
def index():
	return render_template('./index.html')

def get_room_table():
	print(request.referrer)
	# parse room query param from referrer
	try:
		room_query_param = request.referrer.split('?')[1].split('=')[1]
	except:
		room_query_param = None

	if room_query_param is None:
		room_query_param = "public"
	# parse room_query_param to make sure it's safe
	room_query_param = re.sub(r'[^a-zA-Z0-9_]', '', room_query_param)
	return SqliteDict('main.db', tablename=room_query_param, autocommit=True)

def get_messages_key():
	# Current day as string
	day = datetime.datetime.now().strftime("%Y-%m-%d")
	# This is our key in main_table
	main_table = get_room_table()
	if day not in main_table:
		main_table[day] = []
	return day

def get_message_history():
	# Get message lists sorted by date
	main_table = get_room_table()
	keys = sorted(main_table.keys())
	ret = []
	for key in keys:
		ret.extend(main_table[key])
	return ret

@socketio.on('connected')
def conn(msg):
	return {'data':'Ok', 'messages': get_message_history()}

@socketio.on('client_message')
def receive_message(data):
	main_table = get_room_table()
	# Current day as string
	day = get_messages_key()
	data['date'] = datetime.datetime.now().isoformat()
	day_messages = main_table[day]
	day_messages.append(data)
	main_table[day] = day_messages

	# Send the message to all clients
	emit('server_message', data, broadcast=True)

if __name__ == '__main__':
	socketio.run(app, debug=True, host="0.0.0.0", port=5001)
