# U27 Menu Manager

A digital menu management system with slideshow capabilities, designed for displaying menu items and promotional content on secondary displays.

## Features

### Image Management
- **Upload Images**: 
  - Drag & drop interface
  - Click to upload
  - Supports PNG, JPG, JPEG, GIF, BMP, WEBP, HEIF, HEIC formats
  - Visual feedback during upload

### Image Organization
- **Grid View**: 
  - Thumbnail display of all uploaded images
  - Image name and upload time information
  - Responsive grid layout

### Selection Tools
- **Multi-select Capability**:
  - Click individual images to select
  - "Select All" functionality
  - Visual feedback for selected items
  - Bulk delete selected images

### Slideshow Controls
- **Customizable Display**:
  - Adjustable delay between slides (1-60 seconds)
  - Multiple transition effects
  - Configurable transition duration (0.1-5.0 seconds)

### Device Management
- **Device Naming**:
  - Clickable device name display
  - Persistent device names
  - Server-side storage

### Responsive Design
- Mobile-friendly interface
- Touch-optimized controls
- Adaptive layout for different screen sizes
- Dark mode support

## Technical Details

### Backend
- Built with Flask (Python)
- File-based storage system
- Process management for slideshow display
- JSON-based configuration storage

### Frontend
- Responsive HTML/CSS design
- Vanilla JavaScript
- No external dependencies
- Modern CSS features (CSS Variables, Flexbox, Grid)

### Display
- Pygame-based slideshow renderer
- Smooth transitions
- Full-screen display support
- Error handling for missing images

## Installation

1. Clone the repository
   ```bash
   git clone [repository-url]
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application
   ```bash
   python app.py
   ```

## Usage

1. Access the web interface at `http://localhost:5000`
2. Upload images through drag & drop or file selection
3. Select images for slideshow
4. Configure slideshow settings
5. Start the slideshow

## File Structure
```
U27-Menu-Manager/
├── app.py              # Main Flask application
├── display_image.py    # Slideshow display logic
├── templates/          # HTML templates
│   └── index.html     # Main interface
├── uploads/           # Image storage directory
└── device_name.json   # Device configuration
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Authors

John Zheng | bluevisor@gmail.com
