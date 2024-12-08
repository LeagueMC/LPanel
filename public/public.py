from flask import Flask, render_template, request, redirect, url_for, session
import os
import datetime
import json
import re
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def load_user_data():
    with open('/home/administrator/LPanel/data/user-data.json') as f:
        return json.load(f)

def get_servers_data(servers_dir):
    servers_data = []
    for server_name in os.listdir(servers_dir):
        server_path = os.path.join(servers_dir, server_name)
        if os.path.isdir(server_path):
            creation_time = os.path.getctime(server_path)
            creation_date = datetime.datetime.fromtimestamp(creation_time).strftime("%Y-%m-%d")
            start_script_path = os.path.join(server_path, 'start.sh')
            ram_amount = None
            if os.path.isfile(start_script_path):
                with open(start_script_path, 'r') as f:
                    content = f.read()
                    match = re.search(r'-Xmx(\d+)M', content)
                    if match:
                        ram_amount = f"{match.group(1)} MB"
            servers_data.append({
                'name': server_name,
                'creation_date': creation_date,
                'ram': ram_amount or "N/A"
            })
    return servers_data

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    users = load_user_data()
    for user in users:
        if user['username'] == username and user['password'] == password:
            session['logged_in'] = True
            return redirect(url_for('index'))
    return "Invalid credentials, please try again."

@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/index')
@login_required
def index():
    servers_dir = '/home/administrator/LPanel/servers'
    servers = get_servers_data(servers_dir)
    server_names = [server for server in os.listdir(servers_dir) if os.path.isdir(os.path.join(servers_dir, server))]
    return render_template('index.html', servers=servers, server_names=server_names)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
