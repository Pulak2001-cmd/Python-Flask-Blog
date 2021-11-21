from enum import unique
import os
from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import datetime
import json
import math

from werkzeug.utils import secure_filename

local_server = True
with open('config.json', 'r') as c:
    params = json.load(c)["params"]



app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_folder']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail_user'],
    MAIL_PASSWORD = params['gmail_password']
)
mail = Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)


class Contacts(db.Model):
    '''
    sno, name phone_num, msg, date, email
    '''
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12),unique=True, nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)


class Post(db.Model):
    sno = db.Column(db.Integer,unique=True, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    tagline = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(21),unique=True, nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)
    

@app.route("/")
def home():
    post=Post.query.filter_by().all()
    last = math.ceil(len(post)/int(params['no_of_post']))
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page=1
    page=int(page)
    post=post[(page-1)*int(params['no_of_post']):page*int(params['no_of_post'])]
    if(page == 1):
        prev = "#"
        next = "/?page=" + str(page+1)
    elif(page==last):
        prev = "/?page=" + str(page-1)
        next = "#"
    else:
        prev = "/?page=" + str(page-1)
        next = "/?page=" + str(page+1)
    return render_template('index.html', params=params, post=post, prev=prev, next=next)




@app.route("/about")
def about():
    return render_template('about.html', params=params)

@app.route("/dashboard", methods = ['GET', 'POST'])
def dashboard():
    post = Post.query.all()
    if 'user' in session and session['user'] == params['admin_username']:
        return render_template('dashboard.html', params=params, post = post)
    if request.method == 'POST':
        username= request.form.get('uname')
        password= request.form.get('upassword')
        if(username == params['admin_username'] and password == params['admin_password']):
            session['user'] = username
            return render_template('dashboard.html', params=params, post=post)
        else:
            return render_template('login.html', params=params)

    else:
        return render_template('login.html', params=params)



@app.route("/edit/<string:sno>" , methods=['GET', 'POST'])
def edit(sno):
    if "user" in session and session['user']==params['admin_username']:
        if request.method=="POST":
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()
        
            if sno=='0':
                post = Post(title=box_title, slug=slug, content=content, tagline=tline, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()
                return redirect('/edit/sno')
            else:
                post = Post.query.filter_by(sno=sno).first()
                post.box_title = box_title
                post.tline = tline
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/'+sno)
    else:
        return redirect('/dashboard')

    post = Post.query.filter_by(sno=sno).first()
    return render_template('edit.html', params=params, post=post, serial=sno)

@app.route("/delete/<string:sno>" , methods=['GET', 'POST'])
def delete(sno):
    if 'user' in session and session['user'] == params['admin_username']:
        post = Post.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

@app.route("/uploader", methods = ['GET', 'POST'])
def uploader():
    if "user" in session and session['user'] == params['admin_username']:
        if request.method == "POST":
            f=request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename) ))
            return "Uploader Successfully"
    else:
        return redirect('/dashboard')

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, phone_num = phone, msg = message, date= datetime.now(),email = email )
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New Message from '+ name, sender='email', recipients = [params['gmail_user']], body = message + "\n"+ phone)
    return render_template('contact.html', params=params)

@app.route("/post/<string:post_slug>/<int:post_sno>", methods=['GET'])
def post_route(post_slug,post_sno):
    post = Post.query.filter_by(slug=post_slug, sno=post_sno).first()
    return render_template('post.html', params=params, post=post)

app.run(debug=True)


