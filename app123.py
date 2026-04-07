from flask import Flask, request, redirect, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mysecret123")

app.config['UPLOAD_FOLDER'] = 'uploads'

ADMIN_USER = "admin"
ADMIN_PASS = "1234"

if not os.path.exists('uploads'):
    os.makedirs('uploads')

# ---------------- DB ----------------
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name TEXT,
        email TEXT,
        password TEXT
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        id SERIAL PRIMARY KEY,
        title TEXT,
        company TEXT,
        location TEXT,
        salary TEXT,
        hr TEXT
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS applications (
        id SERIAL PRIMARY KEY,
        user_name TEXT,
        job_id INTEGER,
        resume TEXT,
        status TEXT,
        date TEXT
    )
    ''')

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route('/')
def home():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM jobs")
    jobs = cur.fetchall()
    conn.close()

    html = "<h1>💼 Job Portal</h1>"

    if 'admin' in session:
        html += "<a href='/add_job'>➕ Add Job</a><br><br>"

    for j in jobs:
        html += f"""
        <div>
        <h2>{j[1]}</h2>
        <p>{j[2]} | {j[3]}</p>
        <p>💰 {j[4]}</p>

        📞 <a href='tel:{j[5]}'>Call</a> |
        💬 <a href='https://wa.me/{j[5]}'>WhatsApp</a><br>

        <a href='/apply/{j[0]}'>Apply</a>
        """

        if 'admin' in session:
            html += f"<br><a href='/delete_job/{j[0]}'>❌ Delete</a>"

        html += "</div><hr>"

    html += "<br><a href='/login'>Login</a> | <a href='/admin_login'>Admin</a>"

    return html

# ---------------- ADMIN LOGIN ----------------
@app.route('/admin_login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['user'] == ADMIN_USER and request.form['pass'] == ADMIN_PASS:
            session['admin'] = True
            return redirect('/')
        return "Wrong Admin"

    return '''
    <form method="POST">
    <input name="user" placeholder="Admin ID"><br>
    <input name="pass" placeholder="Password"><br>
    <button>Login</button>
    </form>
    '''

# ---------------- ADD JOB ----------------
@app.route('/add_job', methods=['GET','POST'])
def add_job():
    if 'admin' not in session:
        return redirect('/admin_login')

    if request.method == 'POST':
        title = request.form['title']
        company = request.form['company']
        location = request.form['location']
        salary = request.form['salary']
        hr = request.form['hr']

        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO jobs (title,company,location,salary,hr) VALUES (%s,%s,%s,%s,%s)",
            (title,company,location,salary,hr)
        )

        conn.commit()
        conn.close()

        return redirect('/')

    return '''
    <h2>Add Job</h2>
    <form method="POST">
    <input name="title" placeholder="Job Title"><br>
    <input name="company" placeholder="Company"><br>
    <input name="location" placeholder="Location"><br>
    <input name="salary" placeholder="Salary"><br>
    <input name="hr" placeholder="HR Phone"><br>
    <button>Add Job</button>
    </form>
    '''

# ---------------- DELETE JOB ----------------
@app.route('/delete_job/<int:id>')
def delete_job(id):
    if 'admin' not in session:
        return redirect('/admin_login')

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("DELETE FROM jobs WHERE id=%s", (id,))
    conn.commit()
    conn.close()

    return redirect('/')

# ---------------- SIGNUP ----------------
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method=='POST':
        name=request.form['name']
        email=request.form['email']
        password=generate_password_hash(request.form['password'])

        conn = get_conn()
        cur = conn.cursor()

        cur.execute("INSERT INTO users (name,email,password) VALUES (%s,%s,%s)",
                    (name,email,password))

        conn.commit()
        conn.close()

        return redirect('/login')

    return '''
    <form method="POST">
    <input name="name">
    <input name="email">
    <input name="password">
    <button>Signup</button>
    </form>
    '''

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']

        conn = get_conn()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email=%s",(email,))
        user = cur.fetchone()

        conn.close()

        if user and check_password_hash(user[3], password):
            session['user']=email
            return redirect('/')
        return "Invalid Login"

    return '''
    <form method="POST">
    <input name="email">
    <input name="password">
    <button>Login</button>
    </form>
    '''

# ---------------- APPLY ----------------
@app.route('/apply/<int:id>', methods=['GET','POST'])
def apply(id):
    if 'user' not in session:
        return redirect('/login')

    if request.method=='POST':
        file=request.files['resume']
        filename=str(datetime.now().timestamp())+"_"+file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))

        conn = get_conn()
        cur = conn.cursor()

        cur.execute("INSERT INTO applications (user_name,job_id,resume,status,date) VALUES (%s,%s,%s,%s,%s)",
                    (session['user'],id,filename,'Pending',str(datetime.now())))

        conn.commit()
        conn.close()

        return "Applied Successfully"

    return '''
    <form method="POST" enctype="multipart/form-data">
    <input type="file" name="resume">
    <button>Submit</button>
    </form>
    '''

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run()