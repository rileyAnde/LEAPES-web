import os
import zipfile
import shutil

def rename_and_extract_files(zip_folder_path, output_folder_path):
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)

    file_counter = 1

    for item in os.listdir(zip_folder_path):
        if item.endswith('.zip'):
            zip_path = os.path.join(zip_folder_path, item)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                temp_extract_path = os.path.join(zip_folder_path, 'temp')
                if not os.path.exists(temp_extract_path):
                    os.makedirs(temp_extract_path)
                zip_ref.extractall(temp_extract_path)

                video_file = os.path.join(temp_extract_path, 'out-video.avi')
                key_file = os.path.join(temp_extract_path, 'out-key.csv')

                if os.path.exists(video_file) and os.path.exists(key_file):
                    new_video_name = f'out-video-{file_counter:02d}.avi'
                    new_key_name = f'out-key-{file_counter:02d}.csv'

                    new_video_path = os.path.join(output_folder_path, new_video_name)
                    new_key_path = os.path.join(output_folder_path, new_key_name)

                    shutil.move(video_file, new_video_path)
                    shutil.move(key_file, new_key_path)

                    print(f"Moved {video_file} to {new_video_path}")
                    print(f"Moved {key_file} to {new_key_path}")

                    file_counter += 1
                else:
                    print(f"Files not found in {temp_extract_path}")

def create_final_zip(output_folder_path, final_zip_path):
    with zipfile.ZipFile(final_zip_path, 'w') as final_zip:
        for foldername, _, filenames in os.walk(output_folder_path):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                final_zip.write(file_path, os.path.basename(file_path))
                print(f"Added {file_path} to {final_zip_path}")

if __name__ == '__main__':
    zip_folder_path = r'C:\Users\Riley\LEAPES-web\downloads'
    output_folder_path = os.path.join(zip_folder_path, 'temp')
    final_zip_path = os.path.join(zip_folder_path, 'mega-dataset.zip')

    try:
        rename_and_extract_files(zip_folder_path, output_folder_path)
        create_final_zip(output_folder_path, final_zip_path)
    finally:
        if os.path.exists(output_folder_path):
            shutil.rmtree(output_folder_path)
