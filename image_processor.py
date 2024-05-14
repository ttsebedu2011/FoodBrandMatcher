from tensorflow.keras.preprocessing import image  # Import image preprocessing utilities from Keras
from tensorflow.keras.applications.vgg16 import preprocess_input, VGG16  # Import VGG16 model and preprocessing function
import numpy as np  # Import NumPy for numerical operations
import cv2 as cv  # Import OpenCV for image processing
import os  # Import the os module for interacting with the operating system
import matplotlib.pyplot as plt  # Import matplotlib for plotting
import database  # Import a custom database module for database operations
import json  # Import JSON for serialization/deserialization
from flask import current_app as app

# Load the pre-trained VGG16 model without its top layer (fully connected layers)
model = VGG16(weights='imagenet', include_top=False)

def fetch_image_paths_from_db(db_conn):
    c = db_conn.cursor()
    c.execute("SELECT image_path, feature_vector, ingredients FROM gallery_table")
    rows = c.fetchall()

    # Handling None for feature_vector by setting a default
    result = []
    for row in rows:
        if row[1] is not None:  # Ensuring feature_vector is not None
            path, features, ingredients = row[0], json.loads(row[1]), row[2]
            result.append((path, features, ingredients))
        else:

    # Set a default value for features
            path, ingredients = row[0], row[2]
            default_features = []
            result.append((path, default_features, ingredients))

    return result

def preprocess_image_for_cnn(image_path, target_size=(224, 224)):
    img = image.load_img(image_path, target_size=target_size)  # Load and resize image for VGG16
    img_array = image.img_to_array(img)  # Convert the image to a NumPy array
    img_array_expanded = np.expand_dims(img_array, axis=0)  # Add an extra dimension for batch size
    return preprocess_input(img_array_expanded)  # Preprocess the image array


def extract_features(image_path):

    full_path = os.path.join(app.root_path, image_path)

    processed_img = preprocess_image_for_cnn(full_path)  # Preprocess the image
    features = model.predict(processed_img)  # Predict the features using VGG16
    flattened_features = features.flatten()  # Flatten the features to a 1D array
    return flattened_features  # Return the flattened features


def compare_features(feature1, feature2):
    return np.linalg.norm(feature1 - feature2)  # Calculate and return the Euclidean distance between two feature vectors

def find_best_matches_db(query_image_path, db_conn, num_matches=3):
    query_features = extract_features(query_image_path)
    stored_images = fetch_image_paths_from_db(db_conn)

    matches_info = []

    # Unpack all three elements from each tuple in stored_images
    for img_path, feature_vector_json, ingredients in stored_images:
        # Skip if feature_vector is empty
        if len(feature_vector_json) == 0:
            continue

        stored_features = np.array(feature_vector_json)
        if query_features.shape != stored_features.shape:
            print(f"Skipping incompatible feature vector for image: {img_path}")
            continue

        distance = compare_features(query_features, stored_features)
        matches_info.append((img_path, distance, ingredients))  # Include ingredients in the appended tuple

    # Sort matches by distance and select the top 'num_matches'
    sorted_matches = sorted(matches_info, key=lambda x: x[1])[:num_matches]

    return sorted_matches

def show_images_with_ingredients(query_image_path, matches_info):
    plt.figure(figsize=(12, 8))

    # Load and display the query image
    query_img = cv.cvtColor(cv.imread(query_image_path), cv.COLOR_BGR2RGB)
    plt.subplot(1, len(matches_info) + 1, 1)
    plt.imshow(query_img)
    plt.title("Query Image")
    plt.axis('off')

    for i, (image_path, _, ingredients) in enumerate(matches_info, start=2):
        img = cv.imread(image_path)
        if img is None:
            print(f"Failed to load image at path: {image_path}")
            continue
        img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        plt.subplot(1, len(matches_info) + 1, i)
        plt.imshow(img)
        title = f"Match {i - 1}\nIngredients: {ingredients[:50]}..."  # Show first 50 characters of ingredients
        plt.title(title, fontsize=8)
        plt.axis('off')

    plt.tight_layout()
    plt.show()

def main():
    db_conn = database.connect_db()  # Connect to the database
    database.create_gallery_table(db_conn)  # Ensure the database table exists

    query_image_path = 'static/query_images/bran_flakes.jpg'  # Path of the query image

    best_matches_info = find_best_matches_db(query_image_path, db_conn)  # Find best matches for the query image

    if best_matches_info:
        print("Best matches found:")  # Inform the user that matches were found
        similar_image_paths = [match[0] for match in best_matches_info]  # Extract paths of similar images
        for match_info in best_matches_info:
            print(f"Image: {match_info[0]}, Distance: {match_info[1]}")  # Print details of each match

        show_images_with_ingredients(query_image_path, similar_image_paths)  # Show the query image and its similar images
    else:
        print("No similar images found.")  # Inform the user if no similar images were found

    db_conn.close()  # Close the database connection

if __name__ == "__main__":
    main()  # Execute the main function if the script is run directly
