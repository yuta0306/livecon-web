import os
import secrets
from flask import Flask, render_template, request, sessions, redirect, session
from flask.helpers import url_for
from flask_socketio import SocketIO, send, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

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
    print(session.get('room_id', None))
    return render_template('room.html', room_id=room_id)

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
    print('received message: ' + data)

@socketio.on('json')
def handle_json(json):
    print('received json: ' + str(json))

@socketio.on('my event')
def handle_my_custom_event(json):
    print('received json: ' + str(json))

@socketio.on('my event', namespace='/test')
def handle_my_custom_namespace_event(json):
    print('received json: ' + str(json))

if __name__ == '__main__':
    socketio.run(app, debug=True)