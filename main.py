from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_mail import Mail
import os
import math
import json
from datetime import datetime


with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD=  params['gmail-password']
)
mail = Mail(app)


if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']

else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)


class Contact(db.Model):
    '''
    sno, name, phone_num, email, message, datetime
    '''
    sno = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.String(), nullable=False)
    datetime = db.Column(db.String(20), nullable=False)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    post_name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(50), nullable=False)
    post_content = db.Column(db.String(25000), nullable=False)
    timestamp = db.Column(db.String(50), nullable=True)
    img_file = db.Column(db.String(30), nullable=True)

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    # [0:params['no_of_posts']]

    # Pagination
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)

    posts = posts[(page - 1)*int(params['no_of_posts']): (page - 1)*int(params['no_of_posts']) + int(params['no_of_posts'])]
    if (page==1):
        prev = "#"
        next = "/?page=" + str(page+1)
    elif(page==last):
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)


    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)

@app.route("/about")
def about():
    return render_template('about.html', params=params)

@app.route("/post/<string:slug>", methods=['GET'])
def post_route(slug):
    post = Posts.query.filter_by(slug=slug).first()
    return render_template('post.html', params=params, post=post)

@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):
    if request.method == 'POST':
        title = request.form.get('title')
        slug = request.form.get('slug')
        img_file = request.form.get('img')
        content = request.form.get('content')
        date = datetime.now()

        post = Posts.query.filter_by(sno=sno).first()
        post.post_name = title
        post.slug = slug
        post.img_file = img_file
        post.post_content = content
        post.timestamp = date
        db.session.commit()
        return redirect('/edit/' + sno)
    post = post = Posts.query.filter_by(sno=sno).first()
    return render_template('edit.html', params=params, post=post)

@app.route("/uploader", methods = ['GET', 'POST'])
def uploader():
    if (request.method=='POST'):
        f = request.files['file']
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
        return 'Uploaded Successfully'

@app.route("/delete/<string:sno>", methods=['GET' , 'POST'])
def delete(sno):
    post = Posts.query.filter_by(sno=sno).first()
    db.session.delete(post)
    db.session.commit()
    return redirect('/dashboard')


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    posts = Posts.query.all()
    if(request.method=='POST'):
        '''Add entry to the database'''
        title = request.form.get('title')
        slug = request.form.get('slug')
        img_file = request.form.get('img')
        content = request.form.get('content')
        entry = Posts(post_name=title, slug = slug, img_file = img_file, post_content= content, timestamp= datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message(title + ' post added successfully',
                          sender='Admin',
                          recipients = [params['gmail-user']],
                          body = 'slug - ' + slug + '\n' + "Img file - " + img_file + "\n" + "\n" "Content :- \n" + content
                          )
    return render_template('dashboard.html', params=params, posts = posts)

@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contact(name=name, phone_num = phone, message = message, datetime= datetime.now(), email = email )
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients = [params['gmail-user']],
                          body = message + "\n" + "Phone Number - " + phone + "\n" + "Email - " + email
                          )

    return render_template('contact.html', params=params)

app.run(debug=True)