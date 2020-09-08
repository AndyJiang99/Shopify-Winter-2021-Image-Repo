import os
from flask import Flask, render_template, url_for, request, session, \
    redirect, send_file, send_from_directory, Response, make_response
from flask_pymongo import PyMongo
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, \
    check_password_hash
from werkzeug.utils import secure_filename
from zipfile import ZipFile
from cryptography.fernet import Fernet
import json
from helper import ALLOWED_EXTENSIONS, listAll, listName, allowed_file

UPLOAD_FOLDER = 'static/uploads'

app = Flask(__name__)

MONGO_URI = os.environ.get('MONGO_URI', None)

app.config['MONGO_URI'] = MONGO_URI
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'mysecret'

mongo = PyMongo(app)


# Key for pictures encryption. Only make a new file if a file doesn't exist yet
# so encryption is persistent
# Storing this here only demonstrating how to do encryption and decryption. In
# production, will be storing key as a env variable
def write_key():
    if os.path.exists('key.key') == False:
        key = Fernet.generate_key()
        with open('key.key', 'wb') as key_file:
            key_file.write(key)


# Load the key itself
def load_key():
    return open('key.key', 'rb').read()


# Homepage. If user is authenticated already, show the dashboard with
# pictures the user already uploaded.
# Returns a page
@app.route('/')
def index():
    if 'username' in session:
        listFiles = []
        allImages = listName()
        for images in allImages:
            listFiles.append(images['filename'])
        return render_template('dashboard.html', name=session['name'],
                               files=listFiles)

    return render_template('index.html')


# Login method
# Returns a page
@app.route('/login', methods=['POST', 'GET'])
def login():

    # If authenticated already, show dashboard
    if 'username' in session:
        return redirect(url_for('index'))

    # If trying to bypass, go back to log in form
    if request.method == 'GET':
        return render_template('index.html', message='Please log in!')

    # Query the username from Mongo storage
    login_user = \
        MongoClient(MONGO_URI).UserLogin.users.find_one({'username': request.form['username'
            ]})

    # If found a user
    if login_user:

        # Check the hash of the password
        if check_password_hash(login_user['password'],
                               request.form['pass']):

            # Sets the current session to the logged in user
            session['username'] = login_user['username']
            session['name'] = login_user['name']
            return redirect(url_for('index'))
        else:
            return render_template('index.html',
                                   message='Invalid username/password combination'
                                   )

    return render_template('register.html',
                           message='User doesn\'t exist. Please sign up to start!'
                           )


# User registration method
# Returns a page
@app.route('/register', methods=['POST', 'GET'])
def register():

    # New registration
    if request.method == 'POST':
        existing_user = \
            MongoClient(MONGO_URI).UserLogin.users.find_one({'username': request.form['username'
                ]})

        # If username doesn't already exist
        if existing_user is None:

            # Encrypt user password
            hashpass = generate_password_hash(request.form['pass'],
                    method='SHA512')

            # Store user information
            MongoClient(MONGO_URI).UserLogin.users.insert_one({'username': request.form['username'
                    ], 'password': hashpass, 'name': request.form['name'
                    ]})

            # Set the current session to the registered user
            session['username'] = request.form['username']
            session['name'] = request.form['name']
            return redirect(url_for('index'))

        return render_template('index.html',
                               message='That username already exists!')

    # Attemping a GET requests ends up here
    return render_template('register.html')


# User uploads images
# Returns the dashboard with the newly uploaded images
@app.route('/upload', methods=['POST'])
def upload():
    if 'username' in session:

        # If user hasn't uploaded any files
        if 'files[]' not in request.files:
            flash('No file part')
            return redirect(request.url)

        # Get the list of all files
        files = request.files.getlist('files[]')
        file_names = []
        for file in files:

            # Check if the file is part of the allowable file extension
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_names.append(filename)

                # Saves the pictures/s to the server
                file.save(os.path.join(app.config['UPLOAD_FOLDER'],
                          filename))

                # Encryption the image into memory
                key = load_key()
                f = Fernet(key)
                with open(os.path.join(app.config['UPLOAD_FOLDER'],
                          filename), 'rb') as imageFile:
                    file_data = imageFile.read()
                encrypted_data = f.encrypt(file_data)

                # Upload encrypted image to Mongo with the filename
                client = MongoClient(MONGO_URI)
                client.ImagesAll.images.insert_one({'username': session['username'
                        ], 'image': encrypted_data,
                        'filename': filename})
            else:
                flash('Allowed image types are -> png, jpg, jpeg, gif')
                return redirect('dashboard.html')

        # Getting the list of all the files the user has
        listFiles = []
        allImages = listName()
        for image in allImages:
            listFiles.append(image['filename'])
    return render_template('uploaded.html', filenames=file_names,
                           name=session['name'], files=listFiles)


# Routing to display the recently uploaded images
# Returns path to image
@app.route('/display/<filename>')
def display_image(filename):
    return redirect(url_for('static', filename='uploads/' + filename),
                    code=301)


# User log out. Clear session username
# Returns log out confirmation
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return render_template('index.html',
                           message='Successfully logged out!')


# Allows the user to be able to download files they have uploaded
# Returns a file to the client
@app.route('/viewPictures', methods=['POST'])
def viewPictures():
    if 'username' in session:

        # Gets all checked images the user wants to download on the dashboard
        toDownload = request.form.getlist('pictures')
        listFiles = []

        # Gets all of the images the user has under their account
        allImages = listAll()

        # Loads the encryption key
        key = load_key()

        # If the pictures.zip doesn't exist on server yet, create it
        if toDownload != []:
            zipObj = ZipFile('pictures.zip', 'w')

        # Goes through all the images the user has
        for image in allImages:

            # If the user wants to download this image
            if image['filename'] in toDownload:
                f = Fernet(key)

                # Decrypt the image data using the key
                decrypt_data = f.decrypt(image['image'])

                # Write to the disk on the backend
                with open(image['filename'], 'wb') as file:
                    file.write(decrypt_data)

                # Writes the image to the zip file
                zipObj.write(image['filename'])

                # Removes the image from the disk
                os.remove(image['filename'])
        zipObj.close()
        zipname = 'pictures.zip'

        # Sends the zip file from the server to the client
        with open(zipname, 'rb') as f:
            data = f.readlines()

            # Remove the zip file from the server itself
            os.remove(zipname)
            return Response(data,
                            headers={'Content-Type': 'application/zip',
                            'Content-Disposition': 'attachment; filename=%s;'
                             % zipname})

    # If not authenticated, go to register page
    return render_template('register.html')


# Allows the user to delete pictures
# Returns the dashboard page with the pictures the user has in the repo
@app.route('/deletePictures', methods=['POST'])
def deletePictures():
    if 'username' in session:

        # Gets the list of pictures the user wants to delete from the checkbox list
        toDelete = request.form.getlist('pictures')
        client = MongoClient(MONGO_URI)
        for image in toDelete:
            client.ImagesAll.images.delete_one({'username': session['username'
                    ], 'filename': image})

        # Gets the list of files for the dashboard after deletion
        listFiles = []
        allImages = listName()
        for image in allImages:
            listFiles.append(image['filename'])
        return render_template('dashboard.html', name=session['name'],
                               files=listFiles)

    # If not authenticated, send back to register page
    return render_template('register.html')

if __name__ == '__main__':
    write_key()
    app.run(threaded=True, port=5000)
