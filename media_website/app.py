from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import sqlite3
import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Change this for production

UPLOAD_FOLDER = 'static/uploads'
DATABASE = 'users.db'
CHAT_LOG = []

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize DB
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0
            )
        ''')
        conn.commit()

init_db()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with get_db_connection() as conn:
            try:
                conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
                conn.commit()
                flash('Registration successful. Please log in.')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Username already exists.')

    return render_template('register.html', current_year=datetime.datetime.now().year)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with get_db_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password)).fetchone()

        if user:
            session['username'] = username
            session['is_admin'] = True
            flash('Login successful.')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.')

    return render_template('login.html', current_year=datetime.datetime.now().year)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    files = os.listdir(UPLOAD_FOLDER)
    return render_template(
        'dashboard.html',
        username=session['username'],
        files=files,
        current_year=datetime.datetime.now().year
    )

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # Make sure the user is logged in
    if 'username' not in session:
        flash('You must log in to access this page.')
        return redirect(url_for('login'))

    # Make sure the user is an admin
    if not session.get('is_admin'):
        flash('Access denied: Admins only.')
        return redirect(url_for('dashboard'))

    # If the form is submitted
    if request.method == 'POST':
        file = request.files.get('media_file')
        media_type = request.form.get('media_type')

        if file and file.filename:
            filename = file.filename

            # OPTIONAL: You can validate allowed extensions if you want
            allowed_extensions = {'mp3', 'mp4', 'avi', 'mkv', 'wav'}
            if '.' in filename:
                ext = filename.rsplit('.', 1)[1].lower()
                if ext not in allowed_extensions:
                    flash('Invalid file type.')
                    return redirect(url_for('admin'))

            # Save the file in static/uploads
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            flash(f'File "{filename}" uploaded successfully!')

        else:
            flash('No file selected.')

    return render_template(
        'admin.html',
        current_year='2024'
    )

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        message = request.form['message']
        username = session['username']
        CHAT_LOG.append(f"{username}: {message}")

    return render_template(
        'chat.html',
        messages=CHAT_LOG,
        current_year=datetime.datetime.now().year
    )

@app.route('/make_admin/<username>')
def make_admin(username):
    with get_db_connection() as conn:
        conn.execute('UPDATE users SET is_admin = 1 WHERE username = ?', (username,))
        conn.commit()
    flash(f'User {username} is now an admin!')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)