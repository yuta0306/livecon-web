import os
import secrets
from flask import Flask, render_template, request, sessions, redirect, session
from flask.helpers import url_for
from flask_socketio import SocketIO, join_room, leave_room, send, emit

debug = False
app = Flask(__name__)
if debug:
    app.config['SECRET_KEY'] = 'secret!'
else:
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
socketio = SocketIO(app)

chat_cache = {}

@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                 endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/room', methods=['GET', 'POST'])
def create_room():
    if request.method == 'POST':
        room_id = secrets.token_urlsafe(16)
        session.update({
            'room_id': room_id,
        })
        return redirect(url_for('room', room_id=room_id))

    else:
        if 'room_id' in session.keys():
            return redirect(url_for('room', room_id=session.get('room_id')))
        return redirect('/')

@app.route('/room/<room_id>')
def room(room_id: str):
    if session.get('room_id', None) is None:
        session.update({'room_id': room_id})
    # if session.get('user_id', None) is None:
    #     user_id = generate_uid()
    #     session.update({'user_id': user_id})
    #     print(session.get('user_id'))
    chats = chat_cache.get(room_id, [])
    
    return render_template('room.html', room_id=room_id,
                            chats=chats,
                            chats_length=len(chats))

def generate_uid():
    return secrets.token_urlsafe(32)

# バックグラウンドでサーバー側から常に情報を与える
# def background(comment):
#     num = 0
#     while True:
#         socketio.sleep(1) # time.sleepでも代用可能。たぶん
#         num += 1
#         content = "<span>%d%s</span>" % (num,comment)
#         '''my_countに送信。後述の@socketio.on()で指定していないときは、socketio.emitとし、namespaceを指定する必要あり。
#         namespaceとmy_countについてはsocket.html内のjQueryで受け取るためのラベルになってます。
#         contentが送信するデータです。'''
#         socketio.emit('my_count', {'data': content}, namespace='/demo')

@socketio.on('message')
def handle_message(data):
    room_id = session.get('room_id')
    print(room_id, data)
    global chat_cache
    if chat_cache.get(room_id) is None:
        chat_cache[room_id] = []
    chat_cache[room_id].append(data['data'])
    emit('message', data, to=room_id)

@socketio.on('join')
def handle_join(data):
    room_id = data.get('data')
    join_room(room_id)
    print('入室', room_id)
    send('入室しました．', to=room_id)
    user_id = generate_uid()
    emit('user_id', {'user_id': user_id}, to=room_id)

@socketio.on('leave')
def handle_leave(data):
    room_id = data.get('data')
    leave_room(room_id)
    print('退室', room_id)
    global chat_cache
    del chat_cache[room_id]
    session.clear()
    send('退室しました', to=room_id)

@socketio.on('reserve prior')
def handle_prior(data):
    room_id = data.get('data')
    emit('prior', data, to=room_id)

@socketio.on('json')
def handle_json(json):
    print('received json: ' + str(json))

@socketio.on('my event')
def handle_my_custom_event(json):
    print('received json: ' + str(json))

# @socketio.on('my event', namespace='/test')
# def handle_my_custom_namespace_event(json):
#     print('received json: ' + str(json))

if __name__ == '__main__':
    if debug:
        socketio.run(app, debug=debug)
    else:
        socketio.run(app, host='0.0.0.0', port=80, debug=debug)