from flask import Flask, render_template, redirect, url_for, jsonify, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
import random
from utils.email_verification import send_verification_code, init_mail

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///memory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
init_mail(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    nickname = db.Column(db.String(150), unique=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    game1_score = db.Column(db.Integer, default=0)
    game2_score = db.Column(db.Integer, default=0)
    game1_plays = db.Column(db.Integer, default=0)  # shu yerda qo'shildi
    game2_plays = db.Column(db.Integer, default=0)  # shu yerda qo'shildi



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        nickname = request.form['nickname']
        email = request.form['email']
        password = request.form['password']
        code = request.form['code']

        if User.query.filter_by(nickname=nickname).first():
            flash('Nickname already exists')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))

        if session.get('verification_code') != code:
            flash('Invalid verification code')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(name=name, nickname=nickname, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Successfully registered. Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/send-code', methods=['POST'])
def send_code():
    email = request.form['email']
    code = str(random.randint(100000, 999999))
    session['verification_code'] = code
    try:
        send_verification_code(email, code)
        return "OK", 200
    except Exception as e:
        print("Email error:", e)
        return "Failed", 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        if name:
            current_user.name = name
        if password:
            current_user.password = generate_password_hash(password)

        db.session.commit()
        flash("Ma'lumotlar muvaffaqiyatli yangilandi!", "success")
        return redirect(url_for('profile'))

    return render_template('profile.html', user=current_user)


@app.route('/game1', methods=['GET', 'POST'])
@login_required
def game1():
    if request.method == 'POST':
        correct_number = session.get('game1_number')
        user_input = request.form['user_input']
        score = 1 if user_input == correct_number else 0

        current_user.game1_plays += 1
        db.session.commit()
        if score > current_user.game1_score:
            current_user.game1_score = score
        db.session.commit()
        return render_template('game1.html', score=score, done=True)
    
    number = ''.join([str(random.randint(0, 9)) for _ in range(5)])
    session['game1_number'] = number
    return render_template('game1.html', number=number, done=False)


@app.route('/game2', methods=['GET', 'POST'])
@login_required
def game2():
    if request.method == 'POST':
        # Bu yerda foydalanuvchi javobini tekshirish va ball berish kodini qo'shing
        current_user.game1_plays += 1
        db.session.commit()
        # Tekshiruv va natijani ko'rsatish...
        return render_template('game2.html', done=True)
    return render_template('game2.html', done=False)

@app.route('/get_words')
@login_required
def get_words():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(base_dir, 'words.txt')
    with open(filepath, encoding='utf-8') as f:
        words = [line.strip() for line in f if line.strip()]
    chosen = random.sample(words, 6)
    return jsonify(chosen)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
