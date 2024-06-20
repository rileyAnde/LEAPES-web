from flask import Flask, request, send_from_directory, jsonify
from flask_cors import CORS
import paramiko
import os
import zipfile

import shutil

app = Flask(__name__, static_folder='static')
CORS(app)

def scp_folder_from_deepracer(deep_racer_ip, src_folder_path, dest_folder_path, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(deep_racer_ip, username=username, password=password)
        sftp = ssh.open_sftp()
        # Download the entire folder from DeepRacer
        for entry in sftp.listdir_attr(src_folder_path):
            filename = entry.filename
            remote_file = os.path.join(src_folder_path, filename)
            local_file = os.path.join(dest_folder_path, filename)
            sftp.get(remote_file, local_file)
        sftp.close()
        ssh.close()
    except Exception as e:
        raise Exception(f"SCP Error: {str(e)}")

def zip_folder(source_dir, zip_file):
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                zf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(source_dir, '..')))

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/download_file', methods=['POST'])
def download_file():
    deep_racer_ip = request.form['deep_racer_ip']
    source_folder = '/home/deepracer/DeepPicar-DeepRacer/dataset'
    zip_file = 'dataset.zip'  # Name for the temporary zip file

    username = 'deepracer'
    password = 'robocar1234'

    try:
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

        # Download the dataset folder from DeepRacer
        scp_folder_from_deepracer(deep_racer_ip, source_folder, 'downloads', username, password)

        # Create a zip archive of the downloaded dataset folder
        zip_folder(os.path.join('downloads', 'dataset'), os.path.join('downloads', zip_file))

        # Clean up the downloaded dataset folder after zipping
        shutil.rmtree(os.path.join('downloads', 'dataset'))

        # Generate the download link for the zip file
        return jsonify({'file_path': f'downloads/{zip_file}'}), 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return str(e), 500
    
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

if not os.path.exists('downloads'):
    os.makedirs('downloads')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

