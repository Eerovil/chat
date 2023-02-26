#! /usr/bin/python
# -*- encoding: utf-8 -*-

import datetime
import re
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from sqlitedict import SqliteDict

app = Flask(__name__, template_folder='templates', static_url_path='/chat/static/', static_folder='static')
SqliteDict('main.db', tablename="main", autocommit=True)

app.config['SECRET_KEY'] = 'eero'
socketio = SocketIO(app)

@app.route('/')
def index():
	return render_template('./index.html')

def get_room():
	# parse room query param from referrer
	try:
		room_query_param = request.referrer.split('?')[1].split('=')[1]
		if room_query_param and '&' in room_query_param:
			room_query_param = room_query_param.split('&')[0]
	except:
		room_query_param = None

	if room_query_param is None:
		room_query_param = "public"
	# parse room_query_param to make sure it's safe
	room_query_param = re.sub(r'[^a-zA-Z0-9_]', '', room_query_param)
	return room_query_param

def get_room_table():
	room_query_param = get_room()
	return SqliteDict('main.db', tablename=room_query_param, autocommit=True)

def get_room_users_table():
	room_query_param = get_room()
	return SqliteDict('main.db', tablename=room_query_param + "_users", autocommit=True)

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
	return {'data':'Ok', 'messages': get_message_history(), 'users': list(get_room_users_table().values())}

@socketio.on("login", namespace="/")
def login(username):
	users_table = get_room_users_table()
	print("login", request.sid, username)
	users_table[request.sid] = {
		"username": username,
		"last_seen": datetime.datetime.now().isoformat(),
		"status": "online",
		"ip": request.sid,
	}
	emit("users", {"users": list(users_table.values())}, broadcast=True)

@socketio.on("disconnect", namespace="/")
def disconnect():
	users_table = get_room_users_table()
	print("disconnect", request.sid)
	if request.sid in users_table:
		user = users_table[request.sid]
		user["status"] = "offline"
		user["last_seen"] = datetime.datetime.now().isoformat()
		users_table[request.sid] = user
	emit("users", {"users": list(users_table.values())}, broadcast=True)

@socketio.on("typing", namespace="/")
def typing(values):
	_typing_status = values["typing"]
	_nickname = values["nickname"]
	print("typing", request.sid, _typing_status)
	users_table = get_room_users_table()
	if request.sid not in users_table:
		users_table[request.sid] = {
			"username": _nickname,
			"last_seen": datetime.datetime.now().isoformat(),
			"status": "online",
			"ip": request.sid,
		}

	user = users_table[request.sid]
	new_status = "online"
	if _typing_status:
		new_status = "typing"
	user["last_seen"] = datetime.datetime.now().isoformat()
	if user["status"] != new_status:
		user["status"] = new_status
		users_table[request.sid] = user
		emit("users", {"users": list(users_table.values())}, broadcast=True)
	else:
		users_table[request.sid] = user

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

@socketio.on('get_bot_response')
def get_bot_response():
	main_table = get_room_table()
	day = get_messages_key()
	room_query_param = get_room()
	if room_query_param == "aibot":
		# Get bot response
		from aibot import ai_complete
		# 10 last messages
		messages = get_message_history()[-10:]
		ai_response = ai_complete(messages)
		if ai_response is None:
			return
		data = {
			"nickname": "Botti",
			"message": ai_response,
		}
		data['date'] = datetime.datetime.now().isoformat()
		day_messages = main_table[day]
		day_messages.append(data)
		main_table[day] = day_messages
		emit('server_message', data, broadcast=True)


if __name__ == '__main__':
	socketio.run(app, debug=True, host="0.0.0.0", port=5005)
