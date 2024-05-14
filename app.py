import json

from flask import Flask, request, jsonify, url_for, session, redirect, render_template, send_from_directory, \
    get_flashed_messages, flash
from keras.src.applications import VGG16
from werkzeug.utils import secure_filename
import os


import database
import image_processor

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

model = None

@app.before_first_request
def load_model():
    global model
    model = VGG16(weights='imagenet', include_top=False)

@app.route('/')
def index():
    print("Index page is being rendered")
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('add_image.html')


@app.route('/upload', methods=['POST'])
# Handles file upload, saving, and storing metadata in the database
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = secure_filename(file.filename)
    # Save the image to the 'static/uploads' folder
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(os.path.join(app.root_path, filepath))

    # Extract ingredients data from form
    ingredients = request.form.get('ingredients', '')

    # Adjust the filepath to use forward slashes, which are compatible with URLs
    filepath_for_db = filepath.replace('\\', '/').replace('static/', '')

    # Insert the uploaded image information into the database, including ingredients
    with database.connect_db() as db_conn:

        database.insert_image_with_ingredients(db_conn, filename, ingredients, filepath_for_db)

    # URL for accessing the uploaded image, ensuring no 'static' duplication
    file_url = url_for('static', filename=filepath_for_db, _external=True)

    print(f"Filepath for saving: {os.path.join(app.root_path, filepath)}")
    print(f"Filepath for DB: {filepath_for_db}")
    print(f"Generated File URL: {file_url}")

    return jsonify({
        'success': True,
        'message': 'File uploaded successfully',
        'filepath': file_url
    })

@app.route('/add_image_to_gallery', methods=['POST'])
# Handles adding images to the gallery including saving and feature extraction
def add_image_to_gallery():
    image = request.files['image']
    ingredients = request.form['ingredients']

    if image and ingredients:
        filename = secure_filename(image.filename)

        # Correct relative path within the 'static/uploads' directory
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Save the image to the filesystem
        try:
            image.save(image_path)
            print(f"Image saved to {image_path}")

            # Extract the features from the image
            feature_vector = image_processor.extract_features(image_path)

            # Insert the data into the database
            with database.connect_db() as db_conn:
                features_json = json.dumps(feature_vector.tolist())

                database.insert_gallery_image_with_features(db_conn, filename, ingredients, image_path, features_json)

            return jsonify(success=True, message="Image added to gallery.")

        except FileNotFoundError as fnf_error:
            print(fnf_error)
            return jsonify(success=False, message="File not found."), 404
        except Exception as e:
            print(f"An error occurred: {e}")
            return jsonify(success=False, message="An error occurred while saving the image."), 500
    else:
        return jsonify(success=False, message="Image or ingredients missing."), 400


@app.route('/search_similar', methods=['POST'])
# Retrieves and displays images similar to the provided one using database matches
def search_similar():
    image_filename = request.form['image_path'].split('/')[-1]
    db_conn = database.connect_db()
    try:
        best_matches_info = image_processor.find_best_matches_db(image_filename, db_conn)
        # Convert each tuple in best_matches_info to a dictionary
        similar_images_info = [
            {
                'path': match[0].replace('\\', '/'),  # Image path
                'distance': match[1],  # Distance
                'ingredients': match[2]  # Ingredients
            }
            for match in best_matches_info
        ]
    finally:
        db_conn.close()
    return render_template('results.html', query_image=image_filename, similar_images=similar_images_info)


@app.route('/upload_and_search', methods=['POST'])
# Handles file upload followed by searching for similar images
def upload_and_search():
    file = request.files['image']
    if file:
        filename = secure_filename(file.filename)
        # Save the file to the UPLOAD_FOLDER
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(os.path.join(app.root_path, filepath))

        db_conn = database.connect_db()
        try:
            full_path = os.path.join(app.root_path, filepath)
            best_matches_info = image_processor.find_best_matches_db(full_path, db_conn)
            similar_images_info = [
                {
                    'path': url_for('static', filename='uploads/' + os.path.basename(match[0])).replace('\\', '/'),
                    'distance': match[1],
                    'ingredients': match[2]
                }
                for match in best_matches_info
            ]
        finally:
            db_conn.close()
        return jsonify({'success': True, 'similar_images_info': similar_images_info})
    return jsonify({'success': False, 'message': "No file uploaded."})


@app.route('/gallery')
# Displays all images in the gallery
def gallery():
    db_conn = database.connect_db()
    try:
        # Fetching all images from the database
        gallery_images = database.fetch_all_gallery_images(db_conn)
        # Preparing the images information, ensuring the paths are correct
        gallery_images_info = [{
            'name': image['image_name'],
            # Correcting the path if it contains an additional 'static/' prefix and ensure forward slashes
            'path': image['image_path'].replace('static/', '', 1).replace('\\', '/') if image['image_path'].startswith('static/') else image['image_path'].replace('\\', '/'),
            'ingredients': image['ingredients']
        } for image in gallery_images]

        # Debug: Printing the corrected gallery_images_info paths to console
        print([image['path'] for image in gallery_images_info])

    finally:
        db_conn.close()

    return render_template('gallery.html', gallery_images_info=gallery_images_info)


@app.route('/image_detail/<image_name>')
# Display detailed information about a specific image
def image_detail(image_name):
    with database.connect_db() as db_conn:
        image_info = database.fetch_image_details_by_filename(db_conn, image_name)

    if image_info:
        image_info['path'] = image_info['path'].replace('static/', '', 1).replace('\\', '/')
        return render_template('image_detail.html', image=image_info)
    else:
        return 'Image not found', 404

@app.route('/about')
def about():
    return render_template('about_us.html')

@app.route('/contact')
def contact():
    return render_template('contact_us.html')



# Run the Flask application
if __name__ == '__main__':
    db_conn = database.connect_db()
    database.create_table(db_conn)
    database.create_gallery_table(db_conn)
    database.create_uploaded_images_table(db_conn)
    database.update_image_paths()
    db_conn.close()
    app.run(debug=True, host='0.0.0.0')
    #app.run(debug=True)