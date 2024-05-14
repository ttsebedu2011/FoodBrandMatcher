# Import the sqlite3 library to work with SQLite databases
import os
import sqlite3
# Import the json library to serialize/deserialize Python lists to/from JSON
import json

# Function to connect to an SQLite database
def connect_db(db_path='image_features2.db'):
    abs_path = os.path.abspath(db_path)
    print(f"Connecting to database at: {abs_path}")
    conn = sqlite3.connect(db_path)
    return conn

# Function to create a table in the database
def create_table(conn):
    """Create the database table for storing image features, if it doesn't already exist"""
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS images
                (image_id INTEGER PRIMARY KEY AUTOINCREMENT, image_path TEXT, feature_vector TEXT, category TEXT)''')
    conn.commit()

# Function to create an additional table for uploaded images
def create_uploaded_images_table(conn):
    """Create the database table for storing uploaded images"""
    c = conn.cursor()
    # SQL command to create a table for uploaded images
    c.execute('''CREATE TABLE IF NOT EXISTS uploaded_images
                (image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_name TEXT,
                image_data BLOB,
                upload_timestamp TEXT)''')
    conn.commit()

def create_gallery_table(conn):
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS gallery_table
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_name TEXT,
                    ingredients TEXT,
                    image_path TEXT,  
                    feature_vector TEXT)''')
        conn.commit()
        print("Gallery table created successfully.")
    except Exception as e:
        print(f"An error occurred while creating gallery_table: {e}")


def image_already_exists(conn, image_name):
    """Check if an image already exists in the gallery_table based on its name"""
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM gallery_table WHERE image_name = ?", (image_name,))
    count = c.fetchone()[0]
    return count > 0

def insert_gallery_image_with_features(conn, image_name, ingredients, image_path, features_json):
    if image_already_exists(conn, image_name):
        print(f"Image {image_name} already exists in the database. Skipping insertion.")
        return

    # To check ingredients is a string, if it's a dictionary, serialize it
    if isinstance(ingredients, dict):
        ingredients_json = json.dumps(ingredients)
    else:
        ingredients_json = ingredients  # ingredients is already a string

    try:
        c = conn.cursor()
        # Insert data into the gallery_table
        c.execute("""
            INSERT INTO gallery_table (image_name, ingredients, image_path, feature_vector)
            VALUES (?, ?, ?, ?)
        """, (image_name, ingredients_json, image_path, features_json))
        conn.commit()
        print(f"Successfully inserted {image_name} into gallery_table.")
    except sqlite3.DatabaseError as e:
        print(f"Database error occurred while inserting {image_name}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while inserting {image_name}: {e}")


# Function to insert an uploaded image into the database
def insert_uploaded_image(conn, image_name, image_data, upload_timestamp):
    """Insert an uploaded image and its metadata into the database"""
    c = conn.cursor()
    # Execute SQL command to insert a new row into the uploaded_images table
    c.execute("INSERT INTO uploaded_images (image_name, image_data, upload_timestamp) VALUES (?, ?, ?)",
            (image_name, image_data, upload_timestamp))
    conn.commit()


# Function to insert an image and its features into the database
def insert_image_feature(conn, image_path, feature_vector, category=""):
    try:
        # Create a cursor object
        c = conn.cursor()
        # Serialize the feature vector to JSON for storage
        feature_vector_json = json.dumps(feature_vector.tolist())
        # Execute SQL command to insert a new row into the images table
        c.execute("INSERT INTO images (image_path, feature_vector, category) VALUES (?, ?, ?)",
                (image_path, feature_vector_json, category))
        # Commit changes to the database
        conn.commit()
    except sqlite3.DatabaseError as e:
        # Handle database errors
        print(f"Database error occurred: {e}")
    except Exception as e:
        # Handle any other exceptions
        print(f"An error occurred: {e}")

# Function to update an existing image's features in the database
def update_image_feature(conn, image_path, feature_vector, category=""):
    """Update an existing image's features in the database"""
    # Serialize the feature vector to JSON
    feature_vector_json = json.dumps(feature_vector.tolist())
    # Create a cursor object
    c = conn.cursor()
    # Execute SQL command to update feature_vector and category for the given image path
    c.execute("UPDATE images SET feature_vector = ?, category = ? WHERE image_path = ?",
            (feature_vector_json, category, image_path))
    # Commit changes to the database
    conn.commit()

def update_image_paths(db_path='image_features2.db'):
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Select all images
    cursor.execute("SELECT id, image_path FROM gallery_table")
    images = cursor.fetchall()

    for img_id, path in images:
        # Remove 'static/' prefix if present and ensure no leading '/'
        new_path = path.replace('static/', '').lstrip('/')
        # Update the database
        cursor.execute("UPDATE gallery_table SET image_path=? WHERE id=?", (new_path, img_id))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

# Function to delete an image's features from the database
def delete_image_feature(conn, image_path):
    """Delete an image's features from the database based on its path"""
    # Create a cursor object
    c = conn.cursor()
    # Execute SQL command to delete the row corresponding to the given image path
    c.execute("DELETE FROM images WHERE image_path = ?", (image_path,))
    # Commit changes to the database
    conn.commit()

def delete_uploaded_image(conn, image_name):
    """Delete an uploaded image's metadata from the database"""
    c = conn.cursor()
    # Execute SQL command to delete the row corresponding to the given image name
    c.execute("DELETE FROM uploaded_images WHERE image_name = ?", (image_name,))
    # Commit changes to the database
    conn.commit()

# Function to fetch all image features stored in the database
def fetch_all_features(conn):
    """Fetch all image features stored in the database"""
    # Create a cursor object
    c = conn.cursor()
    # Execute SQL command to select three columns from the images table
    c.execute("SELECT image_id, image_path, feature_vector FROM images")
    # Fetch all records from the query result
    rows = c.fetchall()
    # Return the list of rows
    return rows


def fetch_all_gallery_images(conn):
    images = []
    try:
        c = conn.cursor()
        c.execute("SELECT image_name, image_path, ingredients FROM gallery_table")
        rows = c.fetchall()
        for row in rows:
            image_name, image_path, ingredients_json = row
            try:
                ingredients = json.loads(ingredients_json)
            except json.JSONDecodeError:
                print(f"Invalid JSON for image {image_name}: {ingredients_json}")
                ingredients = "Invalid ingredients data"
            images.append({
                'image_name': image_name,
                'image_path': image_path,
                'ingredients': ingredients
            })
    except Exception as e:
        print(f"An error occurred while fetching gallery images: {e}")
    return images


def fetch_image_details_by_filename(conn, filename):
    """
    Fetches image details by filename from the gallery_table
    Args:
        conn: Database connection object
        filename: Name of the image file
    Returns:
        A dictionary with image details if found, otherwise None
    """
    # Create a cursor object using the connection
    c = conn.cursor()
    # Execute a query to select the image details based on the filename
    c.execute("SELECT image_name, ingredients, image_path FROM gallery_table WHERE image_name = ?", (filename,))
    # Fetch one record from the query result
    image_info = c.fetchone()

    if image_info:

        return {
            'name': image_info[0],
            'ingredients': image_info[1],
            'path': image_info[2]
        }
    else:
        return None



def get_image_info_by_name(image_name):
    conn = sqlite3.connect('image_features2.db')
    cur = conn.cursor()
    cur.execute("SELECT image_name, image_path, ingredients FROM gallery_table WHERE image_name = ?", (image_name,))
    image_info = cur.fetchone()
    conn.close()
    if image_info:
        return {
            'name': image_info[0],
            'path': image_info[1],
            'ingredients': image_info[2]
        }
    else:
        return None


def insert_image_with_ingredients(conn, image_name, ingredients, image_path):
    """
    Insert image details into the gallery_table if it does not already exist
    - conn: Database connection object
    - image_name: Name of the image file
    - ingredients: Ingredients associated with the image
    - image_path: Path to the image file, relative from the 'static' directory
    """
    print(f"Checking if image already exists in the database: {image_name}")

    # Correcting the path to ensure it's relative from 'static/uploads'
    relative_image_path = os.path.join('uploads', os.path.basename(image_path))

    if not image_exists(conn, relative_image_path):
        try:
            c = conn.cursor()
            c.execute("""
                INSERT INTO gallery_table (image_name, ingredients, image_path)
                VALUES (?, ?, ?)
            """, (image_name, ingredients, relative_image_path))
            conn.commit()
            print(f"Successfully inserted {image_name} with ingredients into gallery_table.")
        except Exception as e:
            print(f"An error occurred while inserting image with ingredients: {e}")
    else:
        print(f"Image {image_name} already exists in the gallery_table. Skipping insertion.")

def image_exists(conn, image_path):
    """Check if an image already exists in the gallery_table based on its path"""
    c = conn.cursor()
    c.execute("SELECT id FROM gallery_table WHERE image_path = ?", (image_path,))
    result = c.fetchone()
    return result is not None


def fetch_all_uploaded_images_with_ingredients(conn):
    """Fetch all uploaded images and their ingredients from the database"""
    c = conn.cursor()
    c.execute("SELECT image_name, ingredients, image_path FROM gallery_table")
    rows = c.fetchall()
    images = [
        {'name': row[0], 'ingredients': row[1], 'image_path': row[2]}
        for row in rows
    ]
    return images


# Function to fetch and print images
def fetch_and_print_all_images(conn):
    """Fetch and print all image entries from the database"""
    # Create a cursor object
    c = conn.cursor()
    # Execute SQL command to select all columns from the images table
    c.execute("SELECT * FROM images")
    # Fetch all records from the query result
    rows = c.fetchall()

    # Loop through each row in the result
    for row in rows:
        # Deserializing feature_vector for readability
        image_id, image_path, feature_vector, category = row
        feature_vector = json.loads(feature_vector)
        # Print the image ID, path, first ten features, and category
        print(f"ID: {image_id}, Path: {image_path}, Features: {feature_vector[:10]}..., Category: {category}")

def delete_specific_images(db_path='image_features2.db', image_paths=[]):
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for path in image_paths:
        # SQL command to delete entries with specific image paths
        cursor.execute("DELETE FROM gallery_table WHERE image_path LIKE ?", (path,))

    # Commit the changes
    conn.commit()

    print("Specified images have been deleted from gallery_table.")

    # Close the database connection
    conn.close()

def remove_duplicates(conn):
    """
    Remove duplicate images from the gallery_table
    This function assumes that a duplicate is determined by an identical image name
    Adjust the criteria as necessary for your application
    """
    print("Removing duplicates from gallery_table...")

    try:
        c = conn.cursor()

        # Find duplicate image names and their counts
        c.execute("""
            SELECT image_name, COUNT(*)
            FROM gallery_table
            GROUP BY image_name
            HAVING COUNT(*) > 1
        """)
        duplicates = c.fetchall()

        # Iterate over the result and delete duplicates while leaving one entry
        for image_name, count in duplicates:
            print(f"Found {count} instances of {image_name}. Removing duplicates...")

            # Get the ids of all duplicate entries
            c.execute("""
                SELECT id FROM gallery_table
                WHERE image_name = ?
            """, (image_name,))
            ids = [row[0] for row in c.fetchall()]

            # Keep the first id and prepare to delete the rest
            ids_to_delete = ids[1:]  # all ids except the first one

            # Execute delete command for the duplicates
            c.execute(f"""
                DELETE FROM gallery_table
                WHERE id IN ({','.join('?' for _ in ids_to_delete)})
            """, ids_to_delete)

        conn.commit()
        print("Duplicates removed successfully")
    except Exception as e:
        print(f"An error occurred while removing duplicates: {e}")

def delete_image_and_associated_data(conn, image_name):
    """
    Delete an image and all associated data from all tables based on image name
    Args:
        conn: Database connection object
        image_name: The name of the image to be deleted
    """
    try:
        c = conn.cursor()
        # Delete from gallery_table
        c.execute("DELETE FROM gallery_table WHERE image_name = ?", (image_name,))
        # Delete from uploaded_images
        c.execute("DELETE FROM uploaded_images WHERE image_name = ?", (image_name,))
        # Delete from images if image_path contains the image name
        c.execute("DELETE FROM images WHERE image_path LIKE ?", ('%' + image_name + '%',))
        # Commit the changes
        conn.commit()
        print(f"Successfully deleted all entries associated with {image_name}.")
    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()


# Main block to execute functions when the script is run directly
if __name__ == "__main__":
    db_conn = connect_db()
    create_table(db_conn)
    create_gallery_table(db_conn)
    update_image_paths()
    remove_duplicates(db_conn)
    fetch_and_print_all_images(db_conn)
    #delete_image_and_associated_data(db_conn, 'image_to_delete.jpg')

    print("Fetching gallery images with ingredients...")
    gallery_images = fetch_all_gallery_images(db_conn)
    for image in gallery_images:
        print(f"Gallery Image: {image['image_name']}, Ingredients: {image['ingredients']}, Path: {image['image_path']}")

    db_conn.close()

