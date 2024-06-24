from flask import Flask, request, send_from_directory, jsonify, session, url_for
from flask_cors import CORS
import paramiko
import os
import zipfile
import shutil
import uuid  # For generating unique IDs for downloads

app = Flask(__name__, static_folder='static')
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # Change this to a secure secret key
CORS(app)

def scp_folder_from_deepracer(deep_racer_ip, src_folder_path, dest_folder_path, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(deep_racer_ip, username=username, password=password)
        sftp = ssh.open_sftp()
        # Download the entire folder from DeepRacer
        for entry in sftp.listdir_attr(src_folder_path):
            print(entry)
        remote_file1 = '/home/deepracer/DeepPicar-DeepRacer/dataset/out-key.csv'
        remote_file2 = '/home/deepracer/DeepPicar-DeepRacer/dataset/out-video.avi'
        local_file1 = os.path.join(dest_folder_path, "out-key.csv")
        local_file2 = os.path.join(dest_folder_path, "out-video.avi")
        sftp.get(remote_file1, local_file1)
        sftp.get(remote_file2, local_file2)
        sftp.close()
        ssh.close()
    except Exception as e:
        raise Exception(f"SCP Error: {str(e)}")

def zip_folder(source_dir, zip_file):
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                zf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), source_dir))

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/download_file', methods=['POST'])
def download_file():
    deep_racer_ip = request.form['deep_racer_ip']
    source_folder = '/home/deepracer/DeepPicar-DeepRacer/dataset'
    dest_folder = f'downloads/{session["uuid"]}'  # Unique folder for each session
    zip_file = f'downloads/{session["uuid"]}.zip'  # Unique zip file for each session

    username = 'deepracer'
    password = 'robocar1234'

    try:
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)

        # Download the dataset folder from DeepRacer
        print('SCP starting')
        scp_folder_from_deepracer(deep_racer_ip, source_folder, dest_folder, username, password)
        print('SCP done')

        # Create a zip archive of the downloaded dataset folder
        zip_folder(dest_folder, zip_file)

        # Clean up the downloaded dataset folder after zipping
        shutil.rmtree(dest_folder)

        # Provide the download link for the zip file
        download_url = url_for('send_downloaded_file', filename=f'{session["uuid"]}.zip')
        print(f'Download URL: {download_url}')  # Debug logging
        return jsonify({'file_path': download_url}), 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return str(e), 500

@app.route('/downloads/<filename>', methods=['GET'])
def send_downloaded_file(filename):
    file_path = os.path.join('downloads', filename)
    print(f'Sending file from path: {file_path}')  # Debug logging
    return send_from_directory('downloads', filename)

@app.route('/upload_script', methods=['POST'])
def upload_script():
    deep_racer_ip = request.form['deep_racer_ip']
    file = request.files['file']
    filename = file.filename
    file.save(os.path.join('uploads', filename))
    
    username = 'deepracer'
    password = 'robocar1234'
    dest_file_path = '/home/deepracer/DeepPicar-DeepRacer'
    if 'tflite' in filename:
        dest_file_path += '/models'
    dest_file_path += f'/{filename}'
    
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

@app.before_request
def before_request():
    if 'uuid' not in session:
        session['uuid'] = str(uuid.uuid4())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

