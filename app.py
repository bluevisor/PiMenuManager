from flask import Flask, request, render_template, redirect, url_for, send_from_directory, jsonify
import os
import subprocess
from datetime import datetime
import signal
import psutil
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ORDER_FILE = 'image_order.json'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Store the current slideshow process
slideshow_process = None

# Add device name storage
DEVICE_NAME_FILE = 'device_name.json'
IMAGE_ORDER_FILE = 'image_order.json'
SLIDESHOW_SETTINGS_FILE = 'slideshow_settings.json'

def load_image_order():
    try:
        if os.path.exists(ORDER_FILE):
            with open(ORDER_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading image order: {e}")
    return {}

def save_image_order(order):
    try:
        with open(ORDER_FILE, 'w') as f:
            json.dump(order, f)
    except Exception as e:
        print(f"Error saving image order: {e}")

def stop_slideshow():
    global slideshow_process
    if slideshow_process:
        # Terminate the display_image.py process
        try:
            process = psutil.Process(slideshow_process.pid)
            for child in process.children(recursive=True):
                child.terminate()
            process.terminate()
            process.wait(timeout=3)  # Wait for process to terminate
        except (psutil.NoSuchProcess, AttributeError, psutil.TimeoutExpired):
            pass
        slideshow_process = None

def load_device_name():
    try:
        if os.path.exists(DEVICE_NAME_FILE):
            with open(DEVICE_NAME_FILE, 'r') as f:
                data = json.load(f)
                return data.get('name', '')
    except Exception as e:
        print(f"Error loading device name: {e}")
    return ''

def save_device_name(name):
    try:
        with open(DEVICE_NAME_FILE, 'w') as f:
            json.dump({'name': name}, f)
        return True
    except Exception as e:
        print(f"Error saving device name: {e}")
        return False

def load_slideshow_settings():
    try:
        if os.path.exists(SLIDESHOW_SETTINGS_FILE):
            with open(SLIDESHOW_SETTINGS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading slideshow settings: {e}")
    return {
        'delay': 10,
        'transition': 'fade',
        'transition_duration': 3.0
    }

def save_slideshow_settings(settings):
    try:
        with open(SLIDESHOW_SETTINGS_FILE, 'w') as f:
            json.dump(settings, f)
        return True
    except Exception as e:
        print(f"Error saving slideshow settings: {e}")
        return False

@app.route('/')
def index():
    # Load saved order and settings
    saved_order = load_image_order()
    slideshow_settings = load_slideshow_settings()
    
    # Get all images from upload folder
    images = []
    files = os.listdir(UPLOAD_FOLDER)
    
    # First add files that are in the saved order
    for filename in saved_order.get('order', []):
        if filename in files:
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            upload_time = datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
            images.append({'name': filename, 'upload_time': upload_time})
            files.remove(filename)
    
    # Then add any remaining files that weren't in the saved order
    for filename in files:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        upload_time = datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        images.append({'name': filename, 'upload_time': upload_time})
    
    return render_template('index.html', images=images, slideshow_settings=slideshow_settings)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        return jsonify({'error': 'Invalid file type'}), 400

    try:
        # Get original filename parts
        original_filename = secure_filename(file.filename)
        name, ext = os.path.splitext(original_filename)
        
        # Start with original name
        filename = original_filename
        counter = 1
        
        # Keep trying new names until we find one that doesn't exist
        while os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
            filename = f"{name}({counter}){ext}"
            counter += 1
        
        # Save the file
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Update the order to include the new file
        saved_order = load_image_order()
        order = saved_order.get('order', [])
        if filename not in order:
            order.append(filename)
            save_image_order({'order': order})
        
        # Get the file's creation time
        upload_time = datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'success': True,
            'filename': filename,
            'upload_time': upload_time,
            'renamed': filename != original_filename
        })
    except Exception as e:
        print(f"Error saving file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return redirect(url_for('index'))

@app.route('/display/<filename>', methods=['POST'])
def display_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    mode = request.form.get('mode', 'fit')
    if os.path.exists(file_path):
        subprocess.run(['python3', 'display_image.py', file_path, mode])
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/slideshow', methods=['POST'])
def slideshow():
    global slideshow_process
    stop_slideshow()  # Stop any existing slideshow
    
    data = request.json
    images = data.get('images', [])
    delay = data.get('delay', 10)
    transition = data.get('transition', 'fade')
    transition_duration = data.get('transition_duration', 3.0)
    
    # Save the settings
    save_slideshow_settings({
        'delay': delay,
        'transition': transition,
        'transition_duration': transition_duration
    })
    
    if images:
        # Create comma-separated list of full image paths
        image_paths = ','.join(os.path.join(UPLOAD_FOLDER, img) for img in images)
        
        # Start new slideshow process
        slideshow_process = subprocess.Popen([
            'python3', 
            'display_image.py', 
            image_paths,
            str(delay),
            transition,
            str(transition_duration)
        ])
    
    return '', 204

@app.route('/stop_slideshow', methods=['POST'])
def stop_slideshow_route():
    stop_slideshow()
    return '', 204

@app.route('/update_order', methods=['POST'])
def update_order():
    order = request.json.get('order', [])
    save_image_order({'order': order})
    return jsonify({'status': 'success'})

@app.route('/delete_images', methods=['POST'])
def delete_images():
    images = request.json.get('images', [])
    if not images:
        return jsonify({'error': 'No images specified'}), 400
    
    # Load current order
    saved_order = load_image_order()
    order = saved_order.get('order', [])
    
    for filename in images:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                # Remove from order if present
                if filename in order:
                    order.remove(filename)
        except Exception as e:
            print(f"Error deleting {filename}: {e}")
            return jsonify({'error': f'Failed to delete {filename}'}), 500
    
    # Save updated order
    save_image_order({'order': order})
    return jsonify({'status': 'success'})

@app.route('/get_device_name')
def get_device_name():
    name = load_device_name()
    return jsonify({'name': name})

@app.route('/set_device_name', methods=['POST'])
def set_device_name():
    name = request.json.get('name', '').strip()
    if not name:
        return jsonify({'status': 'error', 'message': 'Name cannot be empty'}), 400
    
    if save_device_name(name):
        return jsonify({'status': 'success', 'name': name})
    return jsonify({'status': 'error', 'message': 'Failed to save device name'}), 500

@app.route('/get_slideshow_settings')
def get_slideshow_settings():
    settings = load_slideshow_settings()
    return jsonify(settings)

@app.route('/save_settings', methods=['POST'])
def save_settings():
    settings = request.json
    if save_slideshow_settings(settings):
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Failed to save settings'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 