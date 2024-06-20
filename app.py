from flask import Flask, request, send_from_directory, jsonify
from flask_cors import CORS
import paramiko
import os

app = Flask(__name__, static_folder='static')
CORS(app)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/download_file', methods=['POST'])
def download_file():
    deep_racer_ip = request.form['deep_racer_ip']
    src_file_path = '/home/deepracer/DeepPicar-DeepRacer/dataset/dataset.tar.gz'
    username = 'deepracer'
    password = 'robocar1234'
    
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    
    dest_file_path = os.path.join('downloads', 'dataset.tar.gz')
    
    try:
        scp_file_from_deepracer(deep_racer_ip, src_file_path, dest_file_path, username, password)
        return jsonify({'file_path': f'downloads/dataset.tar.gz'}), 200
    except Exception as e:
        return str(e), 500

def scp_file_from_deepracer(deep_racer_ip, src_file_path, dest_file_path, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(deep_racer_ip, username=username, password=password)
        sftp = ssh.open_sftp()
        sftp.get(src_file_path, dest_file_path)
        sftp.close()
        ssh.close()
    except Exception as e:
        raise Exception(f"SCP Error: {str(e)}")

@app.route('/uploads/<filename>', methods=['GET'])
def send_uploaded_file(filename):
    return send_from_directory('uploads', filename)

@app.route('/upload_script', methods=['POST'])
def upload_script():
    deep_racer_ip = request.form['deep_racer_ip']
    file = request.files['file']
    filename = file.filename
    file.save(os.path.join('uploads', filename))
    
    username = 'deepracer'
    password = 'robocar1234'
    dest_file_path = f'/home/deepracer/DeepPicar-DeepRacer/{filename}'
    
    try:
        scp_file_to_deepracer(deep_racer_ip, os.path.join('uploads', filename), dest_file_path, username, password)
        return 'File uploaded and transferred successfully', 200
    except Exception as e:
        return str(e), 500

def scp_file_to_deepracer(deep_racer_ip, src_file_path, dest_file_path, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(deep_racer_ip, username=username, password=password)
        sftp = ssh.open_sftp()
        sftp.put(src_file_path, dest_file_path)
        sftp.close()
        ssh.close()
    except Exception as e:
        raise Exception(f"SCP Error: {str(e)}")

@app.route('/run_script', methods=['POST'])
def run_script():
    deep_racer_ip = request.form['deep_racer_ip']
    script_name = request.form['script_name']
    username = 'deepracer'
    password = 'robocar1234'
    
    try:
        output = ssh_run_script(deep_racer_ip, f'python3 /home/deepracer/DeepPicar-DeepRacer/{script_name}', username, password)
        return jsonify({'output': output}), 200
    except Exception as e:
        return str(e), 500

def ssh_run_script(deep_racer_ip, command, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(deep_racer_ip, username=username, password=password)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode() + stderr.read().decode()
        ssh.close()
        return output
    except Exception as e:
        raise Exception(f"SSH Error: {str(e)}")

if not os.path.exists('uploads'):
    os.makedirs('uploads')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

