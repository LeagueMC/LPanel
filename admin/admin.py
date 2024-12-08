from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
import requests  
import shutil  
from functools import wraps


app = Flask(__name__)
app.template_folder = '/home/administrator/LPanel/admin'
app.static_folder = '/home/administrator/LPanel/admin/img'
app.secret_key = 'your_very_secure_secret_key_here'


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def load_user_data():
    if not os.path.exists('/home/administrator/LPanel/data/user-data.json'):
        return []  
    with open('/home/administrator/LPanel/data/user-data.json', 'r') as f:
        try:
            user_data = json.load(f)
            if not isinstance(user_data, list):
                print("Warning: User data is not a list. Resetting to empty list.")
                return []  
            return user_data
        except json.JSONDecodeError:
            print("Error: Invalid JSON format. Returning empty user data.")
            return []  


def save_user_data(user_data):
    with open('/home/administrator/LPanel/data/user-data.json', 'w') as f:
        json.dump(user_data, f, indent=4)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        correct_username = 'admin'
        correct_password = 'Sudden@61'

        if username == correct_username and password == correct_password:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password.')

    return render_template('login.html')

@app.route('/index')
@login_required
def index():
    return render_template('index.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

def create_server(server_name, version, build, ram):
    server_path = f"/home/administrator/LPanel/servers/{server_name}"

    if os.path.exists(server_path):
        return f"<span style='color: #ff3333;'>Server '{server_name}' already exists.</span>"

    
    os.makedirs(server_path)

    
    build_url = f"https://papermc.io/api/v2/projects/paper/versions/{version}/builds/{build}/downloads/paper-{version}-{build}.jar"
    response = requests.get(build_url, stream=True)
    if response.status_code == 200:
        with open(f"{server_path}/server.jar", 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
    else:
        return f"<span style='color: #ff3333;'>Failed to download PaperMC version {version}, build {build}.</span>"

    
    start_script = f"#!/bin/bash\njava -Xmx{ram}M -Xms{ram}M -jar server.jar nogui"
    with open(f"{server_path}/start.sh", 'w') as f:
        f.write(start_script)

    os.chmod(f"{server_path}/start.sh", 0o755) 
    return f"<span style='color: #00cc88;'>Server '{server_name}' created successfully with version {version}, build {build}, and {ram}MB RAM.</span>"


def create_user(user_data, command):
    parts = command.split()
    if len(parts) != 3:
        return jsonify({"output": "<span style='color: #ff3333;'>Usage: create &lt;username&gt; &lt;password&gt;</span>"})

    username, password = parts[1], parts[2]
    for user in user_data:
        if isinstance(user, dict) and user.get('username') == username: 
            return jsonify({"output": f"<span style='color: #ff3333;'>User '{username}' already exists.</span>"})

    new_user = {"username": username, "password": password}
    user_data.append(new_user)
    save_user_data(user_data)
    return jsonify({"output": f"<span style='color: #00cc88;'>User '{username}' created successfully.</span>"})

def delete_user(user_data, command):
    parts = command.split()
    if len(parts) != 2:
        return jsonify({"output": "<span style='color: #ff3333;'>Usage: delete &lt;username&gt;</span>"})

    username_to_delete = parts[1].strip()
    new_user_data = [user for user in user_data if user['username'] != username_to_delete]

    if len(new_user_data) == len(user_data):
        
        return jsonify({"output": f"<span style='color: #ff3333;'>User '{username_to_delete}' does not exist.</span>"})

    save_user_data(new_user_data)
    return jsonify({"output": f"<span style='color: #00cc88;'>User '{username_to_delete}' deleted successfully.</span>"})

def list_users(user_data):
    if not user_data:
        return jsonify({"output": "<span style='color: #ff3333;'>No users to display.</span>"})

    user_list = "<br>".join([f"<span style='color: #ffffff;'>{i + 1}. {user['username']}</span>" for i, user in enumerate(user_data)])
    return jsonify({"output": f"<span style='color: #ffffff;'>Users:<br>{user_list}</span>"})

@app.route('/execute-command', methods=['POST'])
@login_required
def execute_command():
    data = request.json
    command = data.get('command').strip()
    is_server_mode = data.get('isServerMode', False)

    user_data = load_user_data() 

    if is_server_mode:
        if command.startswith('create'):
            parts = command.split()
            if len(parts) != 5:
                return jsonify({"output": "<span style='color: #ff3333;'>Usage: create &lt;name&gt; &lt;version&gt; &lt;build&gt; &lt;RAM&gt;</span>"})
            server_name, version, build, ram = parts[1], parts[2], parts[3], parts[4]
            try:
                ram = int(ram)
                return jsonify({"output": create_server(server_name, version, build, ram)})
            except ValueError:
                return jsonify({"output": "<span style='color: #ff3333;'>RAM must be an integer.</span>"})

        elif command.startswith('delete'):
            parts = command.split()
            if len(parts) != 2:
                return jsonify({"output": "<span style='color: #ff3333;'>Usage: delete &lt;server_name&gt;</span>"})
            server_name = parts[1]
            server_path = f"/home/administrator/LPanel/servers/{server_name}"
            if os.path.exists(server_path):
                shutil.rmtree(server_path)
                return jsonify({"output": f"<span style='color: #00cc88;'>Server '{server_name}' deleted successfully.</span>"})
            else:
                return jsonify({"output": f"<span style='color: #ff3333;'>Server '{server_name}' does not exist.</span>"})

        elif command == 'clear':
            return jsonify({"output": "<span style='color: #00cc88;'>Console cleared.</span>"})

        elif command == 'exit':
            return jsonify({"output": "<span style='color: #ffcc00;'>Exited server mode.</span>"})

        else:
            return jsonify({"output": "<span style='color: #ff3333;'>Unknown command in server mode.</span>"})

    else:
        if command.startswith('create'):
            return create_user(user_data, command)

        elif command.startswith('delete'):
            return delete_user(user_data, command)

        elif command.startswith('list'):
            return list_users(user_data)

        elif command == 'help':
            return jsonify({
                "output": (
                    "<span style='color: #00cc88;'>Available commands:</span><br>" +
                    "<strong>User Management:</strong><br>" +
                    "<span style='color: #00cc88;'>1. create &lt;username&gt; &lt;password&gt;</span> - Create a new user<br>" +
                    "<span style='color: #00cc88;'>2. delete &lt;username&gt;</span> - Delete a user<br>" +
                    "<span style='color: #00cc88;'>3. list</span> - List all users<br>" +
                    "<strong>Server Management:</strong><br>" +
                    "<span style='color: #00cc88;'>4. create &lt;name&gt; &lt;version&gt; &lt;build&gt; &lt;RAM&gt;</span> - Create a new server<br>" +
                    "<span style='color: #00cc88;'>5. delete &lt;server_name&gt;</span> - Delete a server<br>" +
                    "<span style='color: #00cc88;'>6. clear</span> - Clear console<br>" +
                    "<span style='color: #00cc88;'>7. exit</span> - Exit server mode<br>"
                )
            })

    return jsonify({"output": "<span style='color: #ff3333;'>Unknown command.</span>"})

if __name__ == '__main__':
    app.run(host='192.168.0.101', port=8000)
