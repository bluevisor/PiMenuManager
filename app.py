from flask import Flask, request, render_template, redirect, url_for, send_from_directory, jsonify, Response
import os
import subprocess
from datetime import datetime
import signal
import psutil
import json
from werkzeug.utils import secure_filename
from queue import Queue, Empty
from threading import Lock
from PIL import Image
import io
import hashlib
from functools import lru_cache
import random
import argparse
import sys

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ORDER_FILE = 'image_order.json'
DEVICE_NAME_FILE = 'device_name.json'
IMAGE_ORDER_FILE = 'image_order.json'
SLIDESHOW_SETTINGS_FILE = 'slideshow_settings.json'
SLIDESHOW_STATE_FILE = 'slideshow_state.json'
SELECTED_IMAGES_FILE = 'selected_images.json'
MAX_IMAGES = 49  # Maximum number of images allowed

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Store the current slideshow process
slideshow_process = None

# Store SSE clients
clients = []
clients_lock = Lock()

THUMBNAIL_SIZE = (512, 512)  # Increased from (150, 150)
THUMBNAIL_CACHE = {}  # In-memory cache for thumbnails

def notify_clients(event_type, data):
    with clients_lock:
        dead_clients = []
        for client in clients:
            try:
                client.put({
                    'event': event_type,
                    'data': data
                })
            except:
                dead_clients.append(client)
        
        # Remove dead clients
        for client in dead_clients:
            clients.remove(client)

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
        try:
            slideshow_process.terminate()
            slideshow_process.wait(timeout=1)
        except:
            slideshow_process.kill()
        finally:
            slideshow_process = None
            save_slideshow_state(False)

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

def load_selected_images():
    try:
        if os.path.exists(SELECTED_IMAGES_FILE):
            with open(SELECTED_IMAGES_FILE, 'r') as f:
                data = json.load(f)
                return data.get('selected', [])
    except Exception as e:
        print(f"Error loading selected images: {e}")
    return []

def save_selected_images(selected):
    try:
        with open(SELECTED_IMAGES_FILE, 'w') as f:
            json.dump({'selected': selected}, f)
        return True
    except Exception as e:
        print(f"Error saving selected images: {e}")
        return False

def load_slideshow_state():
    try:
        if os.path.exists(SLIDESHOW_STATE_FILE):
            with open(SLIDESHOW_STATE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('active', False)
    except Exception as e:
        print(f"Error loading slideshow state: {e}")
    return False

def save_slideshow_state(active):
    try:
        with open(SLIDESHOW_STATE_FILE, 'w') as f:
            json.dump({'active': active}, f)
        return True
    except Exception as e:
        print(f"Error saving slideshow state: {e}")
        return False

def generate_thumbnail(filename):
    """Generate a thumbnail for an image and cache it"""
    try:
        # Check if thumbnail is in cache
        if filename in THUMBNAIL_CACHE:
            return THUMBNAIL_CACHE[filename]
        
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(file_path):
            return None
        
        # Open and create thumbnail
        with Image.open(file_path) as img:
            # Convert to RGB if necessary (handles PNG with transparency)
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, 'black')
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Remove problematic profiles
            if 'icc_profile' in img.info:
                img.info.pop('icc_profile')
            
            img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            
            # Save to bytes
            thumb_io = io.BytesIO()
            img.save(thumb_io, 'JPEG', quality=85, icc_profile=None)
            thumb_io.seek(0)
            
            # Cache the thumbnail using filename as key
            THUMBNAIL_CACHE[filename] = thumb_io.getvalue()
            return THUMBNAIL_CACHE[filename]
    except Exception as e:
        print(f"Error generating thumbnail for {filename}: {e}")
        return None

def is_slideshow_running():
    """Check if slideshow process is actually running"""
    global slideshow_process
    if slideshow_process is None:
        return False
    
    try:
        # Check if process is still running
        if slideshow_process.poll() is None:
            return True
        else:
            # Process has ended, clean up
            slideshow_process = None
            save_slideshow_state(False)
            return False
    except:
        # If there's any error, assume not running
        slideshow_process = None
        save_slideshow_state(False)
        return False

@app.route('/')
def index():
    # Load initial state
    saved_order = load_image_order()
    slideshow_settings = load_slideshow_settings()
    device_name = load_device_name()
    selected_images = load_selected_images()
    
    # Check actual slideshow state instead of relying on saved state
    slideshow_active = is_slideshow_running()
    save_slideshow_state(slideshow_active)  # Update state file to match reality
    
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
    
    # Then add any remaining files
    for filename in files:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        upload_time = datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        images.append({'name': filename, 'upload_time': upload_time})
    
    return render_template('index.html', 
                         images=images, 
                         slideshow_settings=slideshow_settings,
                         slideshow_active=slideshow_active,
                         device_name=device_name,
                         selected_images=selected_images,
                         max_images=MAX_IMAGES)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        return jsonify({'error': 'Invalid file type'}), 400

    # Check max images limit
    current_images = len(os.listdir(UPLOAD_FOLDER))
    if current_images >= MAX_IMAGES:
        return jsonify({'error': f'Maximum {MAX_IMAGES} images allowed'}), 400

    try:
        # Get original filename and secure it
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        
        # Only modify filename if it already exists
        counter = 1
        while os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
            filename = f"{name}({counter}){ext}"
            counter += 1
        
        # Save the file
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Load current order and append new file
        saved_order = load_image_order()
        order = saved_order.get('order', [])
        if filename not in order:
            order.append(filename)  # Add to end of list
            save_image_order({'order': order})
        
        # Get all files in upload directory
        existing_files = set(os.listdir(UPLOAD_FOLDER))
        
        # Build ordered image list
        images = []
        
        # First add files that are in the saved order
        for fname in order:
            if fname in existing_files:
                fpath = os.path.join(UPLOAD_FOLDER, fname)
                upload_time = datetime.fromtimestamp(os.path.getctime(fpath)).strftime('%Y-%m-%d %H:%M:%S')
                images.append({'name': fname, 'upload_time': upload_time})
                existing_files.remove(fname)
        
        # Then add any remaining files
        for fname in sorted(existing_files):
            fpath = os.path.join(UPLOAD_FOLDER, fname)
            upload_time = datetime.fromtimestamp(os.path.getctime(fpath)).strftime('%Y-%m-%d %H:%M:%S')
            images.append({'name': fname, 'upload_time': upload_time})
        
        # Notify clients about the updated image list
        notify_clients('image_list', {'images': images})
        
        return jsonify({
            'success': True,
            'filename': filename
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
    stop_slideshow()
    
    data = request.json
    images = data.get('images', [])
    settings = {
        'delay': data.get('delay', 10),
        'transition': data.get('transition', 'fade'),
        'transition_duration': data.get('transition_duration', 3.0)
    }
    
    # Save settings and notify clients
    if save_slideshow_settings(settings):
        notify_clients('slideshow_settings', settings)
    
    if images:
        image_paths = ','.join(os.path.join(UPLOAD_FOLDER, img) for img in images)
        slideshow_process = subprocess.Popen([
            'python3', 
            'display_image.py', 
            image_paths,
            str(settings['delay']),
            settings['transition'],
            str(settings['transition_duration'])
        ])
        save_slideshow_state(True)
        notify_clients('slideshow_state', {'active': True})
    
    return '', 204

@app.route('/stop_slideshow', methods=['POST'])
def stop_slideshow_route():
    stop_slideshow()
    save_slideshow_state(False)
    notify_clients('slideshow_state', {'active': False})
    return '', 204

@app.route('/update_order', methods=['POST'])
def update_order():
    order = request.json.get('order', [])
    save_image_order({'order': order})
    notify_clients('image_order', {'order': order})
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
                # Clear thumbnail from cache using filename
                if filename in THUMBNAIL_CACHE:
                    del THUMBNAIL_CACHE[filename]
        except Exception as e:
            print(f"Error deleting {filename}: {e}")
            return jsonify({'error': f'Failed to delete {filename}'}), 500
    
    # Save updated order
    save_image_order({'order': order})
    
    # Get all files in upload directory
    existing_files = set(os.listdir(UPLOAD_FOLDER))
    
    # Build ordered image list
    images = []
    
    # First add files that are in the saved order
    for filename in order:
        if filename in existing_files:
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            upload_time = datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
            images.append({'name': filename, 'upload_time': upload_time})
            existing_files.remove(filename)
    
    # Then add any remaining files that weren't in the order
    for filename in sorted(existing_files):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        upload_time = datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        images.append({'name': filename, 'upload_time': upload_time})
    
    # Notify clients about the updated image list
    notify_clients('image_list', {'images': images})
    
    return jsonify({'status': 'success'})

@app.route('/get_device_name')
def get_device_name():
    name = load_device_name()
    return jsonify({'name': name})

@app.route('/set_device_name', methods=['POST'])
def set_device_name():
    name = request.json.get('name', '').strip()
    # Allow empty names, just save whatever was sent
    if save_device_name(name):
        # Notify all clients about the name change
        notify_clients('device_name', {'name': name})
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
        # Notify all clients about the settings change
        notify_clients('slideshow_settings', settings)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Failed to save settings'}), 500

@app.route('/events')
def events():
    def generate():
        client_queue = Queue()
        with clients_lock:
            clients.append(client_queue)
        
        try:
            while True:
                try:
                    event = client_queue.get(timeout=20)  # 20 second timeout
                    event_data = f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"
                    yield event_data
                except Empty:  # Fixed: Use imported Empty exception
                    yield "data: ping\n\n"  # Keep connection alive
                except GeneratorExit:  # Client disconnected
                    break
                except Exception as e:  # Other errors
                    print(f"SSE Error: {e}")
                    break
        finally:
            # Always clean up the client connection
            with clients_lock:
                if client_queue in clients:
                    clients.remove(client_queue)
            try:
                # Try to drain the queue to prevent resource leaks
                while not client_queue.empty():
                    client_queue.get_nowait()
            except:
                pass
    
    return Response(generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
    })

@app.route('/update_selected', methods=['POST'])
def update_selected():
    selected = request.json.get('selected', [])
    if save_selected_images(selected):
        notify_clients('selected_images', {'selected': selected})
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Failed to save selected images'}), 500

@app.route('/thumbnail/<filename>')
def thumbnail(filename):
    if not os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
        return '', 404
    
    try:
        thumb_data = generate_thumbnail(filename)
        if thumb_data:
            return Response(thumb_data, mimetype='image/jpeg')
        return '', 500
    except Exception as e:
        print(f"Error serving thumbnail for {filename}: {e}")
        return '', 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PiMenu Manager')
    parser.add_argument('--start', action='store_true', help='Start slideshow with saved settings')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the service on (default: 5000)')
    args = parser.parse_args()
    
    # Validate port number
    if args.port < 1 or args.port > 65535:
        print("Error: Port number must be between 1 and 65535")
        sys.exit(1)
    
    if args.start:
        # Load saved settings and selected images
        settings = load_slideshow_settings()
        selected_images = load_selected_images()
        
        if not selected_images:
            print("No images selected for slideshow. Please select images first.")
            sys.exit(1)
            
        # Prepare image paths
        image_paths = [os.path.join(UPLOAD_FOLDER, img) for img in selected_images]
        if not any(os.path.exists(path) for path in image_paths):
            print("No selected images found in uploads folder.")
            sys.exit(1)
            
        # Start slideshow process
        slideshow_process = subprocess.Popen([
            'python3',
            'display_image.py',
            ','.join(image_paths),
            str(settings['delay']),
            settings['transition'],
            str(settings['transition_duration'])
        ])
        save_slideshow_state(True)
    
    print(f"Starting service on port {args.port}")
    app.run(host='0.0.0.0', port=args.port) 