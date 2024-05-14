Food Brand Matcher
Project Overview
Food Brand Matcher is a Flask-based web application that allows users to upload images of food items and match them with a database of food brands. It utilizes the VGG16 deep learning model for image feature extraction and a custom-built database for storing and retrieving food brand information.

Features
Image Upload: Upload food images and extract relevant features.
Gallery: View all uploaded images along with their details.
Search Similar Images: Find similar images from the database based on the uploaded image.
Image Details: View detailed information about a specific image.
Contact and About Pages: Basic static pages providing information about the application.
Setup and Installation
Prerequisites
Python 3.7 or higher
Flask
Keras
TensorFlow
Other dependencies listed in requirements.txt

Project Structure

food-brand-matcher/
│
├── static/
│   ├── uploads/  # Directory for uploaded images
│   └── css/     # CSS files
│
├── templates/
│   ├── index.html
│   ├── add_image.html
│   ├── results.html
│   ├── gallery.html
│   ├── image_detail.html
│   ├── about_us.html
│   └── contact_us.html
│
├── database.py   # Database connection and operations
├── image_processor.py  # Image processing and feature extraction
├── app.py        # Main Flask application
└── requirements.txt

Usage
Home Page
Access the home page at http://localhost:5000/ where you can upload an image or navigate to other pages.

Upload Image
Navigate to the "Upload" page to upload a food image. The image and its metadata will be stored in the database.

Gallery
Visit the "Gallery" page to view all uploaded images with their details. Click on any image to view more information.

Search Similar Images
Use the "Search Similar" functionality to find images in the database that are similar to the one you uploaded.

About and Contact
Static pages providing information about the application and how to contact the developers.

API Endpoints
GET /
Renders the index page.

GET /home
Renders the image upload page.

POST /upload
Handles file uploads and stores image metadata in the database.

POST /add_image_to_gallery
Adds an image to the gallery with feature extraction.

POST /search_similar
Searches for similar images in the database based on the uploaded image.

POST /upload_and_search
Handles file upload and immediately searches for similar images.

GET /gallery
Displays all images in the gallery.

GET /image_detail/<image_name>
Displays detailed information about a specific image.

GET /about
Renders the "About Us" page.

GET /contact
Renders the "Contact Us" page.

Acknowledgments
Thanks to my Supervisors during research and implementation phase.
