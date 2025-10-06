from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import csv
from flask import Response
import os
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from flask import send_from_directory
import uuid
import logging
from sqlalchemy import or_
from markupsafe import Markup, escape
import re
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session, flash
from datetime import timedelta


app = Flask(__name__)



#configure upload folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'docx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#create upload folder if it doesn't exist
os.makedirs('uploads', exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#configure database

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///contacts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#define a model for contact form submissions
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(200), nullable=True) #store file_path if uploaded

migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

app.secret_key = "arpitsecretkey26"
app.permanent_session_lifetime = timedelta(days=7) #sessions last 7 days
@app.route('/')
@app.route('/index')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')

#handle form submission
@app.route('/submit_contact', methods=["POST"])
def submit_contact():
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']

    file = request.files.get('file')
    filename = None
    if file and file.filename != '' and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
    #save to database
    new_contact = Contact(name=name, email=email, message=message, file_path=filename)
    db.session.add(new_contact)
    db.session.commit()

    return redirect(url_for('thank_you'))



@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/admin')
def admin():

    if 'user_id' not in session:
        flash("Please log in to access the admin panel.", "warning")
        return redirect(url_for('login'))

    query = request.args.get("q")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 5, type=int)
    sort = request.args.get("sort", "newest")
    if query:
        base_query = Contact.query.filter(
            or_(Contact.name.contains(query), Contact.email.contains(query), Contact.message.contains(query))
        )
    else:
        base_query = Contact.query
    
    if sort == "newest":
        base_query = base_query.order_by(Contact.id.desc())
    elif sort == "oldest":
        base_query = base_query.order_by(Contact.id.asc())
    elif sort == "name_asc":
        base_query = base_query.order_by(Contact.name.asc())
    elif sort == "name_desc":
        base_query = base_query.order_by(Contact.name.desc())

    contacts = base_query.paginate(page=page, per_page=per_page)

    return render_template('admin.html', contacts=contacts, query=query, per_page=per_page, sort=sort)

@app.route('/delete/<int:id>')
def delete_contact(id):
    contact_to_delete = Contact.query.get_or_404(id)
    db.session.delete(contact_to_delete)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/delete_file/<int:id>')
def delete_file(id):
    contact = Contact.query.get_or_404(id)
    if contact.file_path:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], contact.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        contact.file_path = None #clear file_path in DB
        db.session.commit()
    return redirect(url_for('admin'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_contact(id):
    contact = Contact.query.get_or_404(id)
    if request.method == 'POST':
        contact.name = request.form['name']
        contact.email = request.form['email']
        contact.message = request.form['message']

        #handle file removal
        if request.form.get('remove_file'):
            if contact.file_path:
                old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], contact.file_path)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
                contact.file_path = None #clear file_path in DB

        #handle file upload
        file = request.files.get('file')
        if file and file.filename != '' and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"

            #remove old file if exists
            if contact.file_path:
                old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], contact.file_path)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)

            #save new file
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            contact.file_path = filename #update DB record


        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('edit_contact.html', contact=contact)


@app.template_filter('highlight')
def highlight(text, query):
    if not query:
        return text
    #Escape text and query to prevent XSS
    safe_text = escape(text)
    safe_query = escape(query)

    #regex for whole word match, case-insensitive
    pattern = re.compile(safe_query, re.IGNORECASE)

    highlighted = pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", safe_text)
    
    return Markup(highlighted)

@app.route('/export_csv')
def export_csv():
    # get all contacts
    contacts = Contact.query.order_by(Contact.id.desc()).all()

    # create CSV in memory
    def generate():
        yield 'ID,NAME,EMAIL,MESSAGE\n' #header
        for c in contacts:
            #Escape commas in message
            message = c.message.replace(',', ' ')
            yield f"{c.id},{c.name},{c.email},{message}\n"

    # return as a downloadable file
    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=contacts.csv"}) 

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file part"
        file = request.files['file']
        if file.filename == '':
            return "No selected file"
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return f"File {filename} uploaded successfully!"
    return render_template('upload.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))
        
        #confirm password
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('register'))
        
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = request.form.get('remember') #checkbox value

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username

            if remember:
                session.permanent = True #session lasts for app.permanent_session_lifetime
            else:
                session.permanent = False #session lasts until browser is closed

            flash('Login successful!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


if __name__ == '__main__':

    # Create database tables (run once at the start)
    with app.app_context():
        db.create_all()

    app.run(debug=True)