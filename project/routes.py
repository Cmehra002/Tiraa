import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, g
from sqlalchemy.sql import func
from flask_login import login_user, current_user, logout_user, login_required
from flask_socketio import SocketIO, send, emit, join_room
from werkzeug.security import check_password_hash, generate_password_hash
from flask_bcrypt import check_password_hash as bcrypt_check_password_hash

import os, secrets, random
from PIL import Image
from functools import wraps
from datetime import datetime
from sqlalchemy import or_, and_

from project import app, db, bcrypt, socketio
from project.forms import (RegisterationForm, LoginForm, AnchorForm, CreateNewsForm, 
                           DeleteNewsForm, UpdateAccountForm, ChangePasswordForm)
from project.model import User, Post, Follow, Like, News

# Auth Decorator
def logout_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# Welcome Page
@app.route('/')
@logout_required
def welcome():
    news1 = News.query.all()
    suggested_users = db.session.query(User).order_by(func.random()).limit(5).all()
    return render_template("main.html", news=news1, suggested_users=suggested_users)

# Home Feed
@app.route('/home')
@login_required
def home():
    user = current_user
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    followed_ids = db.session.query(Follow.following).filter_by(follower=current_user.id).subquery()
    feed_post = Post.query.filter(
        or_(
            Post.user_id == current_user.id,
            and_(Post.is_public == True, Post.user_id.in_(followed_ids))
        )
    ).order_by(Post.date_posted.desc()).all()

    non_followed = User.query.filter(User.id.notin_(followed_ids), User.id != current_user.id).all()
    suggested_users = random.sample(non_followed, min(5, len(non_followed)))
    liked_posts_query = db.session.query(Like.post_id).filter_by(user_id=user.id).all()
    liked_posts = [post_id for post_id, in liked_posts_query]

    return render_template("home.html", suggested_users=suggested_users, user=user, image_file=image_file,
                           liked_posts=liked_posts, feed_post=feed_post)

# ✅ New: Dashboard/Profile Route
@app.route('/dashboard/<username>')
@login_required
def dashboard(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.date_posted.desc()).all()
    return render_template("dashboard.html", user=user, posts=posts)

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegisterationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("welcome"))

# ------------------ Chat Functionality --------------------
chat_rooms = {}
user_sessions = {}

@app.before_request
def before_request():
    g.user = current_user if current_user.is_authenticated else None

@app.route("/chat")
@login_required
def chat_page():
    friends = User.query.join(Follow, Follow.following == User.id).filter(Follow.follower == current_user.id).all()
    return render_template("chat.html", friends=friends, username=current_user.username)

@app.route("/messages/<room>", methods=["GET"])
def get_messages(room):
    return jsonify(chat_rooms.get(room, []))

@socketio.on("connect")
def handle_connect():
    print("New WebSocket connection established.")

@socketio.on("join")
def handle_join(data):
    sid = request.sid
    username = data["username"]
    friend = data["friend"]
    room = get_room_name(username, friend)

    user_sessions[sid] = username
    join_room(room)

    emit("message", {"sender": "System", "text": f"{username} joined the chat."}, room=room)

@socketio.on("send_message")
def handle_send_message(data):
    sender = data["sender"]
    receiver = data["receiver"]
    text = data["text"]

    room = get_room_name(sender, receiver)
    message_data = {"sender": sender, "text": text}

    if room not in chat_rooms:
        chat_rooms[room] = []
    chat_rooms[room].append(message_data)

    emit("message", message_data, room=room)

@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    username = user_sessions.pop(sid, "Unknown User")
    print(f"{username} disconnected.")

def get_room_name(user1, user2):
    return "_".join(sorted([user1, user2]))

# ----------------------------------------------------------

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
