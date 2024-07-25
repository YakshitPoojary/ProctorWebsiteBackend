# ProctorWebsiteBackend

Open terminal in root of your directory and run the following commands to setup this project:

## Create a virtual environment
virtualenv env

## Activate the virtual environment
./env/Scripts/activate

## Install all required libraries only after activating the environment
pip install -r requirements.txt

## Start your backend
cd project/
python manage.py runserver

## Add the db.sqlite3 file in your gitignore when pushing to production