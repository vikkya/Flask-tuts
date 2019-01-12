from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
from werkzeug.utils import secure_filename
import json
import os
import math

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True

app = Flask(__name__)
app.secret_key = "super-secret-key"
app.config['UPLOAD_FOLDER'] = params["upload_location"]
app.config.update(
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params["gmail_user"],
    MAIL_PASSWORD = params["gmail_password"]    
)
mail = Mail(app)

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
else: 
    app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone_num = db.Column(db.String(15), nullable=False)
    message = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(12), nullable=True)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(15), nullable=False)
    tag_line = db.Column(db.String(25), nullable=False)
    content = db.Column(db.String(20), nullable=False)
    slug = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(20), nullable=False)

@app.route("/")
def home():

    posts = Posts.query.filter_by().all()
    last = math.floor(len(posts)/int(params["no_of_posts"]))
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params["no_of_posts"]): (page-1)*int(params["no_of_posts"])+int(params["no_of_posts"])]
    #pagination
    # first page
    if (page == 1):
        prev = '#'
        next = "/?page="+ str(page+1)
    elif (page == last):
        prev = "/?page="+ str(page-1)
        next = '#'
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)
    # middle page
    # last page
    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)

@app.route("/about")
def about():
    return render_template('about.html', params=params)

@app.route("/post/<string:post_slug>", methods=["GET", "POST"])
def post(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)

@app.route("/edit/<string:post_sno>", methods=['GET', 'POST'])
def edit(post_sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            tagline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            if post_sno == '0':
                post = Posts(title=box_title, tag_line=tagline, slug=slug, content=content, img_file = img_file, date = datetime.now())
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(post_sno).first()
                post.title = box_title
                post.tag_line = tagline
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.date = datetime.now()
                db.session.commit()
                return redirect('edit/' + post_sno)
        post = Posts.query.filter_by(sno=post_sno).first()
        return render_template('/edit.html', params=params, post=post, sno=post_sno)

@app.route("/uploader", methods=["GET",  "POST"])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Upload Successful"

@app.route("/login", methods=["GET",  "POST"])
def login():
    if ('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)
    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username == params['admin_user'] and userpass == params['admin_password']):
            #set the session
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts=posts)
            #redirect to adminpanel
    else:
        return render_template('login.html', params=params)

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/login')

@app.route("/delete/<string:post_sno>", methods = ["GET", "POST"])
def delete(post_sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(sno=post_sno).first()
        db.session.delete(post)
        db.session.commit()
        return redirect('/login')


@app.route("/contact", methods = ["GET", "POST"])
def contact():
    if(request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, email = email, phone_num = phone, date = datetime.now(), message = message)
        db.session.add(entry)
        db.session.commit()
        mail.send_message("New Message from " + name, 
                    sender = email, 
                    recipients = [params["gmail_user"]],
                    body = message + '\n'+ phone)
    return render_template('contact.html', params=params)

app.run(debug=True)