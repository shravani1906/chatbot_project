from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from mysql.connector.errors import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
import nltk
from nltk.chat.util import Chat, reflections

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Download NLTK data (only the first time)
nltk.download('punkt')

# Example pairs for the chatbot
pairs = [
    (r'hi|hello', ['Hello!', 'Hi there!']),
    (r'how are you?', ['I am good, thanks!', 'Doing well, how about you?']),
    (r'(.*) your name?', ['My name is SwiftBot.']),
    (r'exit', ['Goodbye!']),
    (r'(.*)', ['I am not sure how to respond to that.'])
]

chatbot = Chat(pairs, reflections)

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='your_db_user',
        password='your_db_password',
        database='chatbot_db'
    )

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid credentials'

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        full_name = request.form['full_name']
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            conn.close()
            return render_template('signup.html', error="Username already exists")

        try:
            cursor.execute('INSERT INTO users (username, password, email, full_name) VALUES (%s, %s, %s, %s)', 
                           (username, hashed_password, email, full_name))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except IntegrityError:
            conn.close()
            return render_template('signup.html', error="Username already exists")

    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    return render_template('dashboard.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_input = ''
    bot_response = ''
    if request.method == 'POST':
        user_input = request.form['user_input']
        bot_response = chatbot.respond(user_input)
        
        # Save chat data to database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO chat_logs (user_id, user_input, bot_response) VALUES (%s, %s, %s)', 
                       (session['user_id'], user_input, bot_response))
        conn.commit()
        conn.close()

    return render_template('chat.html', user_input=user_input, bot_response=bot_response)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT username, email, full_name FROM users WHERE id = %s', (session['user_id'],))
    user = cursor.fetchone()
    conn.close()

    if request.method == 'POST':
        email = request.form['email']
        full_name = request.form['full_name']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET email = %s, full_name = %s WHERE id = %s', 
                       (email, full_name, session['user_id']))
        conn.commit()
        conn.close()

        return redirect(url_for('dashboard'))

    return render_template('profile.html', user=user)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
