import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from PIL import Image

# For local development of environment variables
from dotenv import load_dotenv
load_dotenv()

# --- Cloudinary / Cloud Storage Placeholders ---
# In a real production app, you MUST integrate a cloud storage solution.
# Cloudinary is highly recommended for image management.
# For now, we'll use a dummy URL for display until you integrate it.
# Example Cloudinary integration (you would uncomment and set these up properly):
# import cloudinary
# import cloudinary.uploader
#
# cloudinary.config(
#     cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
#     api_key = os.environ.get('CLOUDINARY_API_KEY'),
#     api_secret = os.environ.get('CLOUDINARY_API_SECRET'),
#     secure = True
# )

app = Flask(__name__)

# --- Configuration ---
# Use DATABASE_URL for Render (PostgreSQL), fallback to SQLite for local development
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ensure SECRET_KEY is set. Crucial for sessions and flashes.
# For production on Render, set this as an environment variable!
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_strong_and_random_secret_key_for_dev_only_replace_me')

db = SQLAlchemy(app)

# --- Database Model ---
class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    # Store the URL to the image in cloud storage, not local path
    image_url = db.Column(db.String(500), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(100), default='Uncategorized')
    tags = db.Column(db.String(500), default='') # Comma-separated tags

    def __repr__(self):
        return f'<Photo {self.filename}>'

# Create database tables
# This will create tables if they don't exist.
# For production, consider using Flask-Migrate for better schema management.
with app.app_context():
    db.create_all()

# --- Helper for Auto-Organization ---
# This function will eventually work with image data fetched from cloud storage
# or by sending the image stream directly to a cloud AI service.
def auto_organize_photo(image_file_stream, original_filename):
    category = 'Uncategorized'
    tags = []

    try:
        # Example 1: Basic categorization based on filename (very basic)
        filename_lower = original_filename.lower()
        if "nature" in filename_lower:
            category = "Nature"
        elif "people" in filename_lower or "person" in filename_lower:
            category = "People"
        elif "city" in filename_lower:
            category = "Cityscapes"
        else:
            category = "Other"

        # IMPORTANT: For real auto-organization, you would:
        # A) Use an image processing library (Pillow, OpenCV) on the image_file_stream
        #    OR
        # B) Send the image_file_stream (or its cloud URL) to a cloud AI API like
        #    Google Cloud Vision API or AWS Rekognition for advanced tagging/categorization.
        #
        # Example with Pillow (assuming image_file_stream is a BytesIO object or similar):
        # from io import BytesIO
        # img = Image.open(BytesIO(image_file_stream.read()))
        # You can then process 'img' object.
        # Remember to reset stream position after reading: image_file_stream.seek(0)

    except Exception as e:
        print(f"Error during auto-organization: {e}")
        # Fallback to default category and tags if anything goes wrong
    
    return category, ", ".join(tags)

# --- Routes ---
@app.route('/')
def index():
    photos = Photo.query.order_by(Photo.upload_date.desc()).all()
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
            original_filename = file.filename
            
            # --- CRITICAL CHANGE: Simulate Cloud Upload / Placeholder ---
            # In a real app, 'file' would be uploaded to Cloudinary, S3, etc.
            # cloudinary.uploader.upload(file) would return a dict with 'url'.
            # For this *fixed* example, we'll use a dummy URL for display.
            # You *must* replace this with actual cloud storage integration.

            # Dummy URL for demonstration purposes.
            # In your actual implementation, this will be the URL returned by Cloudinary/S3.
            # For testing, you could use a public image URL or set up Cloudinary.
            image_public_url = "https://via.placeholder.com/250x150?text=Your+Image+Here" # Placeholder
            
            # If using Cloudinary:
            # try:
            #     upload_result = cloudinary.uploader.upload(file)
            #     image_public_url = upload_result['secure_url']
            # except Exception as e:
            #     flash(f"Error uploading to cloud storage: {e}")
            #     return redirect(request.url)

            # Auto-organize the photo (pass the file stream or URL to it)
            # For this example, we pass the file stream for local processing placeholder.
            # In production, you might pass image_public_url to an AI API.
            file.seek(0) # Reset stream position after potential initial read by werkzeug
            category, tags = auto_organize_photo(file.stream, original_filename)

            # Save photo metadata to database
            new_photo = Photo(
                filename=original_filename, # Original name for display
                image_url=image_public_url, # URL to the image in cloud storage
                category=category,
                tags=tags
            )
            db.session.add(new_photo)
            db.session.commit()

            flash('Photo uploaded successfully!')
            return redirect(url_for('index'))
    return render_template('upload.html')

# Removed local '/uploads/<filename>' route because images will be served from cloud storage.
# The `image_url` in the Photo model will directly point to the public URL.

if __name__ == '__main__':
    # Set host to '0.0.0.0' for local testing within Docker/VMs if needed,
    # but for typical local dev, '127.0.0.1' or no host is fine.
    app.run(debug=True, host='0.0.0.0' if os.environ.get('FLASK_ENV') == 'development' else '127.0.0.1')
