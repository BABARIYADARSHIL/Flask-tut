import requests
from flask import Flask, render_template, request, session, redirect,url_for, jsonify,make_response, abort
from flask import flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
from datetime import datetime, timedelta
from flask_mail import Mail
import os
import json
import math
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from functools import wraps
import jwt
from flask import current_app
from jwt import encode
from flask import jsonify
import requests
from flask_cors import CORS
from sqlalchemy import or_
from flask_swagger_ui import get_swaggerui_blueprint

JWT_EXPIRATION_DELTA = timedelta(hours=1)
with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)


SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = '/static/swagger.yml'  # Our API url (can of course be a local resource)




# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "User API "
    },
    # oauth_config={  # OAuth config. See https://github.com/swagger-api/swagger-ui#oauth2-configuration .
    #    'clientId': "your-client-id",
    #    'clientSecret': "your-client-secret-if-required",
    #    'realm': "your-realms",
    #    'appName': "your-app-name",
    #    'scopeSeparator': " ",
    #    'additionalQueryStringParams': {'test': "hello"}
    # }
)

app.register_blueprint(swaggerui_blueprint, url_prefix = SWAGGER_URL)

CORS(app)
app.secret_key = 'super-secret-key'
app.config['SECRET_KEY'] = 'DARSHIL'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:darshil@localhost:3306/server'
db = SQLAlchemy(app)

CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5500"}})








def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("token")        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            print(data)
            current_user=data['user']
            # print(current_user)
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

class Register(db.Model):
    num = db.Column(db.Integer, primary_key=True)
    username= db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(80), nullable=True)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(25), nullable=False)
    message = db.Column(db.String(80), nullable=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f"Register('{self.username}', '{self.email}')"




@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        username = Register.query.filter_by(username=username, password=password).first()
    
        if username:
            token = jwt.encode({'user': username.num, 'exp': datetime.utcnow() + timedelta(hours=5)}, app.config['SECRET_KEY'])
            # token = jwt.encode(payload, app.config['SECRET_KEY'],algorithm='HS256')
            return jsonify({'message': 'Login successful', 'token': token}), 200
        else:
            return jsonify({'error':'Invalide username or password'}),401

    return "Method not Allowed", 405


@app.route('/protected_route')
@token_required
def protected_route():
    # This route is protected and requires a valid token
    return "This is a protected route"



@app.route('/register' ,methods = ['GET','POST'])
def register_page():
    print(request.method)
    if request.method == 'POST':
        print(request.method)
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        message = request.form.get('message')
        phone = request.form.get('phone')
        entry = Register(username=username,password=password,email=email,message=message,date=datetime.now(),phone=phone)
        db.session.add(entry)
        db.session.commit()
        return "Registered successfully"
    print(request.method)
    return 'Missing required fields!', 400



class Posts(db.Model):
    num = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), unique=True, nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now)


@app.route('/Addpost', methods=['GET','POST'])
@token_required 
def Addpost(current_user):
    print(request.method)
    if request.method == 'POST':
        title = request.form.get('title')
        slug = request.form.get('slug')
        content = request.form.get('content')
        tagline = request.form.get('tagline')
        date = datetime.now()
            # Assuming you have a model named Posts imported
        entry = Posts(title=title, slug=slug, content=content, tagline=tagline, date=date)
        db.session.add(entry)
        db.session.commit()

        return 'Data added to the database successfully!', 200
    else:
        return 'Missing required fields!', 400

@app.route("/edit/<string:num>", methods=['GET', 'PUT'])
@token_required
def edit(current_user, num):
    print(request.method)
    # if 'username' in session:
    if request.method == 'PUT':
        title = request.form.get('title')
        tagline = request.form.get('tagline')
        slug = request.form.get('slug')
        content = request.form.get('content')
        date = datetime.now()

        post = Posts.query.filter_by(num=num).first()
        if post:
            post.title = title
            post.slug = slug
            post.content = content
            post.tagline = tagline
            post.date = date
            db.session.commit()
            return jsonify({'message': 'Post updated successfully'})
        else:
            return jsonify({'error': 'Post not found'})

    elif request.method == 'GET':
        post = Posts.query.filter_by(num=num).first()
        if post:
            post_data = {
                'title': post.title,
                'slug': post.slug,
                'content': post.content,
                'tagline': post.tagline,
                'date': post.date.strftime('%Y-%m-%d %H:%M:%S') if post.date else None
            }
            return jsonify({'post': post_data})
        else:
            return jsonify({'error': 'Post not found'})
    return jsonify({'error': 'Unauthorized access'})


@app.route('/home', methods=['GET', 'POST'])
def home():
    form = SearchForm()
    if 'username':
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 100, type=int)

        # Calculate start and end indices for pagination
        start_index = (page - 1) * limit
        end_index = start_index + limit

        # Query posts for the requested page
        posts = Posts.query.offset(start_index).limit(limit).all()

        
        # posts = Posts.query.all()
        post_list = []
        for post in posts:
            post_data = {
            'num':post.num,
            'title':post.title,
            'date':post.date,
            'content':post.content
            }
            post_list.append(post_data)
            total_post = Posts.query.count()
            print(total_post)
        return jsonify({"post_list":post_list, "total_post":total_post})
    return "Unauthorized", 401


@app.route('/')
def home_page():
    return render_template('index.html')



@app.route("/logout", methods=["post","get"])
def logout():
    session.pop('username', None)
    session.clear()
    return "logout successfuly"
    # return redirect('/login')

@app.route("/delete/<string:num>", methods=["GET","POST","DELETE"])
@token_required
def delete(current_user,num):
    if 'username':
        post= Posts.query.filter_by(num=num).first()
        db.session.delete(post)
        db.session.commit()
        return  "successfully deleted the post with number" + num
    else:
        return "Uanauthorized", 401


@app.route('/post', methods=["POST","GET"])
def get_posts():
    posts=Posts.query.all()
    return posts


@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)


class SearchForm(FlaskForm):
    search = StringField('search', validators=[DataRequired()])
    submit = SubmitField('submit')


    
@app.route('/search', methods=["POST", "GET"])
@token_required
def search(current_user):
    # posts= Posts.query.all()
    search_term = request.json.get('search')
    print(search_term)
    posts = Posts.query.filter(or_(Posts.content.like(f'%{search_term}%'), Posts.title.like(f'%{search_term}%'))).order_by(Posts.num).all()
    
    # Convert Posts objects to dictionaries
    posts_data = []
    for post in posts:
        posts_data.append({
            'num':post.num,
            'title':post.title,
            'date':post.date,
            'content':post.content
            # Add other fields as needed
        })

    for post_data in posts_data:
        print(post_data)
    print(posts_data)
    return jsonify(posts_data)




if __name__ == '__main__':
    app.run(debug=True)
# if __name__ == "__main__":
#     app.run(host="127.0.0.1",port=5500)