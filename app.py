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

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
UPLOAD_FOLDER = 'static/uploads'

auth = json.loads(open("auth.json", 'r').read())

MONGO_URI = auth['MONGO_URI']

app = Flask(__name__)

app.config['MONGO_URI'] = MONGO_URI
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

mongo = PyMongo(app)


def write_key():
    if os.path.exists('key.key') == False:
        key = Fernet.generate_key()
        with open('key.key', 'wb') as key_file:
            key_file.write(key)


def load_key():
    return open('key.key', 'rb').read()


@app.route('/')
def index():
    if 'username' in session:
        listFiles = []
        allImages = listName()
        for doc in allImages:
            listFiles.append(doc['filename'])
        return render_template('dashboard.html', name=session['name'],
                               files=listFiles)

    return render_template('index.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    login_user = \
        MongoClient(MONGO_URI).UserLogin.users.find_one({'username': request.form['username'
            ]})
    if login_user:
        if check_password_hash(login_user['password'],
                               request.form['pass']):
            session['username'] = login_user['username']  # request.form['username']
            session['name'] = login_user['name']
            return redirect(url_for('index'))
        else:
            return render_template('index.html',
                                   message='Invalid username/password combination'
                                   )
    return render_template('index.html',
                           message='User doesn\'t exist. Please sign up to start!'
                           )


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        existing_user = \
            MongoClient(MONGO_URI).UserLogin.users.find_one({'username': request.form['username'
                ]})

        if existing_user is None:
            hashpass = generate_password_hash(request.form['pass'],
                    method='SHA512')
            MongoClient(MONGO_URI).UserLogin.users.insert_one({'username': request.form['username'
                    ], 'password': hashpass, 'name': request.form['name'
                    ]})
            session['username'] = request.form['username']
            session['name'] = request.form['name']
            return redirect(url_for('index'))

        return render_template('index.html',
                               message='That username already exists!')

    return render_template('register.html')


def listAll():
    if 'username' in session:
        client = MongoClient(MONGO_URI)
        documents = \
            list(client.ImagesAll.images.find({'username': session['username'
                 ]}))
        return documents


def listName():
    if 'username' in session:
        client = MongoClient(MONGO_URI)
        documents = \
            list(client.ImagesAll.images.find({'username': session['username'
                 ]}, {'filename': 1}))
        return documents


@app.route('/upload', methods=['POST'])
def upload():
    if 'username' in session:
        if 'files[]' not in request.files:
            flash('No file part')
            return redirect(request.url)
        files = request.files.getlist('files[]')
        file_names = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_names.append(filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'],
                          filename))

                # Encryption
                key = load_key()
                f = Fernet(key)
                with open(os.path.join(app.config['UPLOAD_FOLDER'],
                          filename), 'rb') as imageFile:
                    file_data = imageFile.read()
                encrypted_data = f.encrypt(file_data)

                # with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), "wb") as file:
                #     file.write(encrypted_data)

                client = MongoClient(MONGO_URI)
                client.ImagesAll.images.insert_one({'username': session['username'
                        ], 'image': encrypted_data,
                        'filename': filename})
            else:
                flash('Allowed image types are -> png, jpg, jpeg, gif')
                return redirect('dashboard.html')

        listFiles = []
        allImages = listName()
        for doc in allImages:
            listFiles.append(doc['filename'])
    return render_template('uploaded.html', filenames=file_names,
                           name=session['name'], files=listFiles)


@app.route('/display/<filename>')
def display_image(filename):

    # print('display_image filename: ' + filename)

    return redirect(url_for('static', filename='uploads/' + filename),
                    code=301)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() \
        in ALLOWED_EXTENSIONS


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return render_template('index.html',
                               message='Successfully logged out!')


@app.route('/viewPictures', methods=['POST'])
def viewPictures():
    if 'username' in session:
        toDownload = request.form.getlist('pictures')
        listFiles = []
        allImages = listAll()
        key = load_key()
        if toDownload != []:
            zipObj = ZipFile('pictures.zip', 'w')

        for doc in allImages:
            listFiles.append(doc['filename'])
            if doc['filename'] in toDownload:
                f = Fernet(key)
                decrypt_data = f.decrypt(doc['image'])
                with open(doc['filename'], 'wb') as file:
                    file.write(decrypt_data)
                zipObj.write(doc['filename'])
                os.remove(doc['filename'])
        zipObj.close()
        zipname = 'pictures.zip'
        with open(zipname, 'rb') as f:
            data = f.readlines()
            os.remove(zipname)
            return Response(data,
                            headers={'Content-Type': 'application/zip',
                            'Content-Disposition': 'attachment; filename=%s;'
                             % zipname})
    else:

        return render_template('register.html')


    # return render_template('dashboard.html', name = session['username'], files = listFiles)

@app.route('/deletePictures', methods=['POST'])
def deletePictures():
    if 'username' in session:
        toDelete = request.form.getlist('pictures')
        client = MongoClient(MONGO_URI)
        for image in toDelete:
            client.ImagesAll.images.delete_one({'username': session['username'
                    ], 'filename': image})

        listFiles = []
        allImages = listName()
        for doc in allImages:
            listFiles.append(doc['filename'])
        return render_template('dashboard.html', name=session['name'],
                               files=listFiles)
    else:
        return render_template('register.html')

if __name__ == '__main__':
    app.secret_key = 'mysecret'
    write_key()
    app.run(debug=True)