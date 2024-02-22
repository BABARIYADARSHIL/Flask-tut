from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
# from werkzeug import secure_filename
from datetime import datetime
from flask_mail import Mail
import os
import json
import math

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLODE_FOLDER'] = params['uploder_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME =params['gmail'],
    MAIL_PASSWORD=params['password']
)
# mail = Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:darshil@localhost:3306/codingthunder'

db = SQLAlchemy(app)

class Contact(db.Model):
    num = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), unique=True, nullable=False)
    msg = db.Column(db.String(120), nullable=True)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), unique=True, nullable=False)

class Posts(db.Model):
     num = db.Column(db.Integer, primary_key=True)
     title = db.Column(db.String(80), nullable=False)
     slug = db.Column(db.String(21), unique=True, nullable=False)
     content = db.Column(db.String(120), nullable=False)
     tagline = db.Column(db.String(120), nullable=False)
     date = db.Column(db.String(12), nullable=True)

@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if(request.method == 'POST'):

        '''add entry data'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        entry = Contact(firstName=name, phone_num=phone, msg=message, date=datetime.now(), email=email)
        db.session.add(entry)
        db.session.commit()
        # mail.send_message('new message from' + name,
        #                   sender = email,
        #                   recipients=[params['gmail']],
        #                   body=str(message)+"\n"+ str(phone)
        #                   )

    return render_template('index1.html', params=params)

@app.route("/dashbord",methods=['GET', 'POST'])
def dashbord():
    if('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashbord.html', params=params,posts=posts)

    if request.method =='POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if(username == params['admin_user'] and userpass == params['admin_password']):
            # set the session variable
            session['user'] = username
            posts = Posts.query.all()
        return render_template('dashbord.html',params=params,posts=posts)

    return render_template('login.html',params=params)

@app.route("/edit/<string:num>", methods=['GET', 'POST'])
def edit(num):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            tline= request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            date = datetime.now()

            if num =='0':
                post = Posts(title=box_title, slug=slug, content=content, tagline=tline,date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(num=num).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.tagline = tline
                post.date = date
                db.session.commit()
                return redirect('/edit/'+num)
        post = Posts.query.filter_by(num=num).first()
        return render_template('edit.html',params=params,post=post)

# @app.route("/")
# def home():
#     posts = Posts.query.filter_by().all()
#     # number of post show to home page
#     # [0:params['no_of_posts']]
#     last = math.ceil(len(posts)/int(params['no_of_posts']))
#     page = request.args.get('page')
#     if(not str(page).isnumeric()):
#         page = 1
#         page = int(page)
#         posts= posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+(page-1)*int(params['no_of_posts'])]
#         #pagination_logic
#         #First
#         if(page ==1):
#             prev = "#"
#             next = "/?page="+ str(page+1)
#         elif(page == last):
#             prev="/?page=" + str(page - 1)
#             next = "#"
#         else:
#             prev = "/?page=" + str(page - 1)
#             next="/?page" + str(page +1)
#
#     return render_template('index.html', params=params, posts=posts, prev=prev, next=next)

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    #     # number of post show to home page
    #     # [0:params['no_of_posts']]
    last = math.ceil(len(posts) / int(params['no_of_posts']))
    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    posts = posts[(page - 1) * int(params['no_of_posts']): (page - 1) * int(params['no_of_posts']) + int(params['no_of_posts'])]
    if page == 1:
        prev = "#"
        next_page = "/?page=" + str(page + 1)
    elif page == last:
        prev = "/?page=" + str(page - 1)
        next_page = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next_page = "/?page=" + str(page + 1)

    return render_template('index.html', params=params, posts=posts, next=next_page, prev=prev)


@app.route("/Home")
def current():
    return render_template('index.html', params=params)



@app.route("/uploder", methods=['GET','POST'])
def uploder():
    if ('user' in session and session['user'] == params['admin_user']):
        if(request.method == 'POST'):
            f= request.files['file']
            f.save(os.path.join(app.config['UPLODE_FOLDER'], secure_filename(f.filename) ))
            return "uplode successfully"

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashbord')

@app.route("/delete/<string:num>", methods=['GET', 'POST'])
def delete(num):
    if ('user' in session and session['user'] == params['admin_user']):
        post= Posts.query.filter_by(num=num).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashbord')


@app.route("/post")
def post():

    return render_template('post.html', params=params, post=post)

@app.route("/post/<string:post_slug>",methods=['GET'])
def post_route(post_slug):
     post= Posts.query.filter_by(slug=post_slug).first()
     return render_template('post.html',params=params, post=post)

@app.route("/blog-single")
def blogsinge():
    return render_template('blog-single.html', params=params, post=post)



@app.route("/pricing")
def pricing():
    return render_template('pricing.html', params=params)

@app.route("/project")
def project():
    return render_template('project.html', params=params)

@app.route("/service")
def service():
    return render_template('login.html', params=params)




app.run(debug=True)