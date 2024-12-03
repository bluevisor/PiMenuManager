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

@app.route('/')
def index():
    # Load saved order
    saved_order = load_image_order()
    
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
    
    return render_template('index.html', images=images)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        filename = secure_filename(file.filename)
        base, extension = os.path.splitext(filename)
        counter = 1
        
        # Check for existing file and generate new name if needed
        while os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
            filename = f"{base}_{counter}{extension}"
            counter += 1
        
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        
        # Update the order to include the new file
        saved_order = load_image_order()
        order = saved_order.get('order', [])
        if filename not in order:
            order.append(filename)
            save_image_order({'order': order})
        
        return jsonify({
            'success': True,
            'filename': filename
        })
    return jsonify({'error': 'Invalid file type'}), 400

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
    
    images = request.json.get('images', [])
    delay = request.json.get('delay', 10)
    transition = request.json.get('transition', 'fade')
    transition_duration = request.json.get('transition_duration', 3.0)
    
    print(f"Received parameters: delay={delay}, transition={transition}, transition_duration={transition_duration}")
    
    if images:
        # Create comma-separated list of full image paths
        image_paths = ','.join(os.path.join(UPLOAD_FOLDER, img) for img in images)
        
        # Start new slideshow process with all images and transition duration
        slideshow_process = subprocess.Popen([
            'python3', 
            'display_image.py', 
            image_paths,
            str(delay),
            transition,
            str(transition_duration)  # Make sure transition_duration is passed as a string
        ])
        
        print(f"Started slideshow process with command: python3 display_image.py {image_paths} {delay} {transition} {transition_duration}")
    
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 