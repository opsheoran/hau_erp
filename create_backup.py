import os
import zipfile
from datetime import datetime

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
zip_filename = f'backup_{timestamp}.zip'

def zipdir(path, ziph):
    for root, dirs, files in os.walk(path):
        if '__pycache__' in root or '.git' in root:
            continue
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, os.path.dirname(path))
            ziph.write(file_path, arcname)

try:
    print(f'Creating backup: {zip_filename}...')
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipdir('app', zipf)
        if os.path.exists('run.py'):
            zipf.write('run.py')
        if os.path.exists('config.py'):
            zipf.write('config.py')
    print(f'Successfully created backup: {zip_filename}')
except Exception as e:
    print(f'Error creating backup: {e}')
