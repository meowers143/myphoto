import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from PIL import Image
# import piexif # For extracting EXIF data
# from google.cloud import vision # For Google Cloud Vision API

# Load environment variables (for local development)
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# --- Database Configuration ---
# Use PostgreSQL for Render deployment, SQLite for local development
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Image Upload Configuration ---
# In a real app, use S3, GCS, or Cloudinary.
# For this example, we'll use a local 'uploads' folder.
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_secret_key_for_dev') # Replace with strong secret key in production

# --- Database Model ---
class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    # Add columns for auto-organization features
    category = db.Column(db.String(100), default='Uncategorized')
    tags = db.Column(db.String(500), default='') # Comma-separated tags
    # Add more metadata fields as needed (e.g., date_taken, camera_model)

    def __repr__(self):
        return f'<Photo {self.filename}>'

# Create database tables (run once, e.g., in a separate script or on app startup)
# In production, use Flask-Migrate or a similar tool.
with app.app_context():
    db.create_all()

# --- Helper for Auto-Organization ---
def auto_organize_photo(image_path):
    # This is where your auto-organization logic will go.
    # For now, it's a placeholder.

    category = 'Uncategorized'
    tags = []

    try:
        img = Image.open(image_path)

        # Example 1: Basic EXIF data extraction (requires piexif)
        # if 'exif' in img.info:
        #     exif_dict = piexif.load(img.info['exif'])
        #     if piexif.ImageIFD.DateTimeOriginal in exif_dict['0th']:
        #         date_taken = exif_dict['0th'][piexif.ImageIFD.DateTimeOriginal].decode('utf-8')
        #         # You can parse this date and use it for organization
        #         # For simplicity, we'll just add it to tags here
        #         tags.append(f"date:{date_taken.split(' ')[0].replace(':', '-')}")
        #     if piexif.ImageIFD.Make in exif_dict['0th']:
        #         tags.append(f"camera:{exif_dict['0th'][piexif.ImageIFD.Make].decode('utf-8').strip()}")
        #     if piexif.ImageIFD.Model in exif_dict['0th']:
        #         tags.append(f"model:{exif_dict['0th'][piexif.ImageIFD.Model].decode('utf-8').strip()}")

        # Example 2: Simple categorization based on filename (very basic)
        filename_lower = os.path.basename(image_path).lower()
        if "nature" in filename_lower:
            category = "Nature"
        elif "people" in filename_lower or "person" in filename_lower:
            category = "People"
        elif "city" in filename_lower:
            category = "Cityscapes"
        else:
            category = "Other"

        # Example 3: Using a cloud vision API (requires google-cloud-vision)
        # client = vision.ImageAnnotatorClient()
        # with open(image_path, 'rb') as image_file:
        #     content = image_file.read()
        # image = vision.Image(content=content)
        # response = client.label_detection(image=image)
        # labels = response.label_annotations
        # for label in labels:
        #     tags.append(label.description)
        #     if 'animal' in label.description.lower(): # Example: categorize based on detected labels
        #         category = "Animals"
        #     # You'd have more sophisticated logic here

    except Exception as e:
        print(f"Error during auto-organization: {e}")
        # Fallback to default category and tags
    
    return category, ", ".join(tags)

# --- Routes ---
@app.route('/')
def index():
    photos = Photo.query.order_by(Photo.upload_date.desc()).all()
    # You might want to group photos by category here for display
    # E.g., photos_by_category = {}
    # for photo in photos:
    #     photos_by_category.setdefault(photo.category, []).append(photo)
    return render_template('index.html', photos=photos)

@app.route('/upload', methods=['GET', 'POST'])
def upload_photo():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Auto-organize the photo
            category, tags = auto_organize_photo(file_path)

            # Save photo metadata to database
            new_photo = Photo(filename=filename, category=category, tags=tags)
            db.session.add(new_photo)
            db.session.commit()

            flash('Photo uploaded successfully!')
            return redirect(url_for('index'))
    return render_template('upload.html')

# Serve uploaded images (for local development only, in production use cloud storage URLs)
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return redirect(url_for('static', filename='uploads/' + filename))


if __name__ == '__main__':
    app.run(debug=True)
