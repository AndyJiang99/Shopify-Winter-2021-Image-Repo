ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

# Function to list all of the files under a specific user in Mongo
# Returns a list of all files (including image and image name)
# Used when user attemps to download files
def listAll():
    if 'username' in session:
        client = MongoClient(MONGO_URI)
        documents = \
            list(client.ImagesAll.images.find({'username': session['username'
                 ]}))
        return documents


# Function to list all of the filers under a specific user in Mongo
# Returns ONLY filenames
# Used when loading files to dashboard and deleting files
def listName():
    if 'username' in session:
        client = MongoClient(MONGO_URI)
        documents = \
            list(client.ImagesAll.images.find({'username': session['username'
                 ]}, {'filename': 1}))
        return documents


# Allowable file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() \
        in ALLOWED_EXTENSIONS