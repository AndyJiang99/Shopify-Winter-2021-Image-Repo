# Shopify Image Repository

Shopify Winter 2021 Backend Developer Intern application project
Made by Andy Jiang, with a lot of ☕️☕️☕️

This is my project for the Shopify Winter 2021 Backend Developer Internship application!
This application allows the numerous features for users to use this application as a persistent image repository.
It allows for login, authentication, and registrations of new users. Users can encrypted upload and store their images. Users can also download and delete the images they have uploaded. Users also have the option to show their images as public or not, allowing all other users of the service to view their publicly uploaded images.

### Usage

The application is deployed at: https://shopify-winter-2021-image-repo.herokuapp.com/ \
Staging application with new features (if any) is deployed at: https://shopify-winter2021-staging.herokuapp.com/ \
To run this project locally, follow these steps
1. `git clone` the project
2. Open terminal or command line and run `pip3 install -r requirements.txt`
3. Modify the `MONGO_URI` in `app.py` to your own MongoDB Database
4. Create MongoDB Database with the same schema
5. Run `python3 app.py`
6. Flask server at `https://localhost:5000`

### To use

User first needs to create an account or log into the system.
User can then upload images to the repository and is securely stored in the cloud in MongoDB. The webpage will display the image/s that the user has just uploaded.
User can see the images that they have in the repository. They can select/unselect one/many/all of the images to flag for deletion from the repository or download onto their device.
User can log out, and upon logging back in, user can still see the images previously stored.

### User Screenshots

#### User Registration
![Register](https://github.com/AndyJiang99/Shopify-Winter-2021-Image-Repo/blob/master/Images/Register.png)

#### User Dashboard
![Dashboard](https://github.com/AndyJiang99/Shopify-Winter-2021-Image-Repo/blob/master/Images/DashboardView.png)

##### Successful Upload
![Uploaded](https://github.com/AndyJiang99/Shopify-Winter-2021-Image-Repo/blob/master/Images/Uploaded.png)

#### View Public Images
![Public](https://github.com/AndyJiang99/Shopify-Winter-2021-Image-Repo/blob/master/Images/Public.png)

#### Logout
![Logout](https://github.com/AndyJiang99/Shopify-Winter-2021-Image-Repo/blob/master/Images/Logout.png)

### Current Features

Current features/abilities implemented:
 - **Add new users** to the system
 - Storing user **password in encrypted format** in SHA512 format
 - **Access Control** - Users can only access/view their own images
 - **Access Control** - Users can only delete their own images
 - **Adding one/bulk** image/s to the repository
 - **Deleting one/bulk/all** image/s from the repository
 - **Download one/bulk/all** image/s from the repository
 - **Encrypting** the image that is stored in the database
 - Allowing for **public uploading and viewing** of images if desired

### Planned Future Features

 - Confirmation screen if the user actually wants to delete the selected image/s
 - Use AI to get characteristics of the image
 - Hover to get a preview of the image

### Database Schema
```
users{
    username,
    password,
    name
}

images{
    username,
    image (in binary),
    filename,
    public
}
```

### Routes
```
/
    Welcome page for users. If authenticated, returns their dashboard, if not, returns the login page

/register
    New user registrations

/login
    Users can log in

/logout
    Users can log out

/upload
    Users can upload images

/display/<filename>
    Users can see the images they have just uploaded

/viewPictures
    Users can download images they have uploaded

/deletePictures
    Users can delete images they have uploaded

/viewPublic
    Users can see other pictures users uploaded and marked as public
```

### Flowchart of data flow

![Flowchart](https://github.com/AndyJiang99/Shopify-Winter-2021-Image-Repo/blob/master/Images/Flowchart.png)

```
User/Client ->> Flask Server: User registers.
Flask Server -->> MongoDB: If username doesn't exist, saves registration info
MongoDB -->> Flask Server: Success
Flask Server ->> User/Client: Logs user into dashboard.

User/Client ->> Flask Server: Authenticates.
Flask Server -->> MongoDB: Queries username.
MongoDB -->> Flask Server: If username exists, queries the password in salted hash. Else, empty.
Flask Server ->> User/Client: Success, authentication incorrect, or user doesn't exist.

User/Client ->> Flask Server: Uploads picture/s. User chooses whether public or not.
Flask Server -->> MongoDB: Encrypts the picture then upload to Mongo under username.
MongoDB -->> Flask Server: List of all the image filenames under user account.
Flask Server ->> User/Client: Displays all image filenames user has.

User/Client ->> Flask Server: View public images.
Flask Server -->> MongoDB: Queries for all images that have public field set as true.
MongoDB -->> Flask Server: Downloads all public images with data.
Flask Server ->> User/Client: Displays all public images.

User/Client ->> Flask Server: Delete checked pictures.
Flask Server -->> MongoDB: Creates a delete request for each checked picture 
MongoDB -->> Flask Server: List of all the image filenames under user account.
Flask Server ->> User/Client: Displays all image filenames user has.

User/Client ->> Flask Server: Download checked pictures.
Flask Server -->> MongoDB: Queries all of the images the user has including the image info.
MongoDB -->> Flask Server: Sends the image files.
Flask Server -->> Flask Server: Finds the files the user wants and saves it into a zip
Flask Server ->> User/Client: Downloads the zip to the client.
```