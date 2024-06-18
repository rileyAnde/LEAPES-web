from flask import Flask, request, send_from_directory, jsonify
from flask_cors import CORS
import subprocess
import paramiko
import os

app = Flask(__name__, static_folder='static')
CORS(app)

processes = {}

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/run_script', methods=['POST'])
def run_script():
    script_name = request.form['script_name']
    process = subprocess.Popen(['python3', script_name], stdin=subprocess.PIPE)
    processes[script_name] = process
    return 'Script started'

@app.route('/send_input', methods=['POST'])
def send_input():
    script_name = request.form['script_name']
    input_data = request.form['input_data']
    process = processes.get(script_name)
    if process:
        process.stdin.write(input_data.encode())
        process.stdin.flush()
    return 'Input sent'

@app.route('/scp_file', methods=['POST'])
def scp_file():
    src_server_ip = request.form['src_server_ip']
    src_file_path = '/home/deepracer/DeepPicar-DeepRacer/dataset'
    username = 'deepracer'
    password = 'robocar1234'
    
    # Ensure the downloads directory exists
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    
    # Generate a filename based on the IP address to avoid conflicts
    dest_file_name = f'dataset_from_{src_server_ip.replace(".", "_")}.tar.gz'
    dest_file_path = os.path.join('downloads', dest_file_name)
    
    # SCP file from source server to this server
    scp_file_from_server(src_server_ip, src_file_path, dest_file_path, username, password)
    return jsonify({'file_path': f'downloads/{dest_file_name}'})

def scp_file_from_server(src_server_ip, src_file_path, dest_file_path, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(src_server_ip, username=username, password=password)
    
    sftp = ssh.open_sftp()
    sftp.get(src_file_path, dest_file_path)
    sftp.close()
    ssh.close()

@app.route('/downloads/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory('downloads', filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

