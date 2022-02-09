# all the imports I might or might not need idk lol
import os
import json
import requests
import flask_login
from datetime import datetime
from flask import Flask, render_template, url_for, redirect, flash, request, session
from flask_session import Session
from flask_login import LoginManager, login_required
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
# importing my own stuff yay :)
from models import *

app = Flask(__name__)


# this injects a list of users into all jinja templates
# this approach is bad because the way I check if the current user
# is logged in is to check if this list is empty or not
# I should come up with a better way to do this, probably using flask-login
# but I still kinda don't get how to use it fully
@app.context_processor
def inject_user():
  if session.get('users') is None:
    session['users'] = {}
  return dict(user=session["users"])


# check for environment variable
if not os.getenv("DATABASE_URL"):
  raise RuntimeError("DATABASE_URL is not set")

# configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# set up database and flask-login
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
login_manager = LoginManager()
login_manager.init_app(app)


# flask-login needs this to work properly
@login_manager.user_loader
def load_user(user_id):
  return db.query(User).filter(User.id == user_id).first()


# home route, just renders the home page
@app.route("/")
def index():
  return render_template("index.html")


# register route
# GET : displays the login page
# POST: registers a user to the site and logs them in
@app.route("/register", methods=["GET", "POST"])
def register():
  if request.method == "GET":
    return render_template("register.html")
  else:
    username = request.form['username']
    password = request.form['password']
    user = User(username=username)
    user.set_password(password)
    db.add(user)
    db.commit()
    flask_login.login_user(user)
    session["users"] = user
    flash('signed up', 'success')
    return redirect(url_for('index'))


# login route
# GET : displays the login page
# POST: logs in a user to the site if their credentials are valid
# then redirects to the home page
@app.route("/login", methods=["GET", "POST"])
def login():
  if request.method == "GET":
    return render_template("login.html")
  else:
    username = request.form['username']
    password = request.form['password']
    user = db.query(User).filter(User.username == username).first()
    if user:
      if user.check_password(password):
        flask_login.login_user(user)
        flash('logged in', 'success')
        session["users"] = user
        return redirect(url_for('index'))
      else:
        flash('login failed', 'danger')
        return redirect(url_for('login'))
    else:
      flash('login failed', 'danger')
      return redirect(url_for('login'))


# logout route
# POST: logs a user out then redirects to the home page
# login protected because idk what to do if someone tries to log out
# while not being logged in lol
@app.route("/logout", methods=["POST"])
@login_required
def logout():
  flask_login.logout_user()
  session["users"] = {}
  flash('logged out', 'success')
  return redirect(url_for('index'))


# results route, can only get here by making a post
# request to it, renders the results from the home search
@app.route("/results", methods=["POST"])
def results():
  search = request.form['search']
  books = db.execute(
      f"SELECT * FROM books WHERE isbn LIKE '%{search}%' OR author LIKE '%{search}%' OR title LIKE '%{search}%'"
  ).fetchall()
  return render_template("results.html", books=books)


# book route
# GET : searches by isbn value for it and renders all related info to the book only
# displays the option to post a review if there is currently a user logged in
# POST: commits new review to the databsae before redirecting to the book page again
@app.route("/book/<isbn>", methods=["GET", "POST"])
def book(isbn):
  if request.method == "POST":
    user_id = int(request.form['user_id'])
    repeat = db.execute(f"SELECT user_id FROM reviews WHERE user_id='{user_id}'").fetchone()
    if repeat:
      flash('cannot post more than one review', 'danger')
      return redirect(url_for('book', isbn=isbn))
    else:
      content = request.form['content']
      rating = int(request.form['rating'])
      book_id = request.form['book_id']
      date = datetime.utcnow()
      review = Review(content=content, rating=rating, date=date, user_id=user_id, book_id=book_id)
      db.add(review)
      db.commit()
  res = json.loads(
      requests.get("https://www.googleapis.com/books/v1/volumes", params={
          "q": isbn
      }).text)
  gObj = {
      'count': res['items'][1]['volumeInfo']['ratingsCount'],
      'rating': res['items'][1]['volumeInfo']['averageRating'],
      'image': res['items'][1]['volumeInfo']['imageLinks']['thumbnail']
  }
  book = db.execute(f"SELECT * FROM books WHERE isbn='{isbn}'").fetchone()
  reviews = db.execute(
      f"SELECT reviews.content, reviews.rating, reviews.date, users.username FROM reviews INNER JOIN users ON reviews.user_id=users.id"
  ).fetchall()
  return render_template("book.html", book=book, gObj=gObj, reviews=reviews)


# api route
# GET: returns a json object with all the required data
# returns a 404 if isbn is not found
@app.route("/api/<isbn>")
def api(isbn):
  res = json.loads(
      requests.get("https://www.googleapis.com/books/v1/volumes", params={
          "q": isbn
      }).text)
  if res:
    google = {
        'title': res['items'][1]['volumeInfo']['title'],
        'author': res['items'][1]['volumeInfo']['authors'][0],
        'publishedDate': res['items'][1]['volumeInfo']['publishedDate'],
        'ISBN_10': res['items'][1]['volumeInfo']['industryIdentifiers'][0]['identifier'],
        'ISBN_13': res['items'][1]['volumeInfo']['industryIdentifiers'][1]['identifier'],
        'reviewCount': res['items'][1]['volumeInfo']['ratingsCount'],
        'averageRating': res['items'][1]['volumeInfo']['averageRating']
    }
    return json.dumps(google)
  else:
    return


# acknowledgemnets
# much of the code here comes from the following sources, or was in great part inspired from them

# CS50's lecture videos:
# https://www.youtube.com/watch?v=cc0xt9uuKQo
# https://www.youtube.com/watch?v=j5wysXqaIV8
# https://www.youtube.com/watch?v=24Kf3v7kZyE
# https://www.youtube.com/watch?v=Eda-NmcE5mQ

# tutorials on how to store hashed passwords, and general user and auth information:
# https://dev.to/kaelscion/authentication-hashing-in-sqlalchemy-1bem
# https://www.youtube.com/watch?v=PbcfkA_cmqM
# https://www.digitalocean.com/community/tutorials/how-to-add-authentication-to-your-app-with-flask-login

# flask, flask-login and flask-flash official docs
# https://flask.palletsprojects.com/en/2.0.x/
# https://flask-login.readthedocs.io/en/latest/#flask_login.login_user
# https://flask.palletsprojects.com/en/2.0.x/patterns/flashing/

# there are probably many others I am forgetting to mention
# but I made an effort to mention all the ones I coudl think of
# also, a lot of stackoverflow posts were visited to create this