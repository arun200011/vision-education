from flask import Flask, render_template, request, redirect, url_for, flash, abort
import markdown
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from models import db, User, ContactMessage
from auth import auth

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def load_blogs():
    blogs = []
    blogs_path = 'content/blogs'
    for filename in os.listdir(blogs_path):
        if filename.endswith('.md'):
            path = os.path.join(blogs_path, filename)
            with open(path, 'r', encoding='utf-8') as f:
                md_content = f.read()
                html_content = markdown.markdown(md_content)
                excerpt = html_content[:150] + '...'
                blogs.append({
                    'title': filename.replace('-', ' ').replace('.md', '').title(),
                    'slug': filename.replace('.md', ''),
                    'excerpt': excerpt,
                    'image': url_for('static', filename='images/consult1.jpg')
                })
    return blogs

app.register_blueprint(auth, url_prefix='/auth')

@app.route('/')
def home():
    blogs = load_blogs()
    return render_template('index.html', blogs=blogs)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        if not name or not email or not message:
            flash('Please fill all fields.', 'error')
            return redirect(url_for('contact'))

        contact_msg = ContactMessage(name=name, email=email, message=message)
        db.session.add(contact_msg)
        db.session.commit()
        flash('Your message has been sent successfully!', 'success')
        return redirect(url_for('contact'))

    return render_template('contact.html')

@app.route('/blog/<slug>')
def blog_post(slug):
    path = f'content/blogs/{slug}.md'
    if not os.path.exists(path):
        abort(404)
    with open(path, 'r', encoding='utf-8') as f:
        content = markdown.markdown(f.read())
    return render_template('blog_post.html', title=slug.replace('-', ' ').title(), content=content)

@app.route('/study-mbbs')
def study_mbbs():
    return render_template('study_mbbs.html')

@app.route('/universities')
def universities():
    return render_template('mbbs_universities.html')

@app.route('/study-abroad')
def study_abroad():
    return render_template('study_abroad.html')

@app.route('/knowledge')
def knowledge():
    return render_template('knowledge.html')

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form['email']
    with open('subscribers.txt', 'a') as f:
        f.write(email + '\n')
    flash('Subscribed successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Unauthorized access')
        return redirect(url_for('home'))

    blogs = load_blogs()
    messages = ContactMessage.query.all()
    users = User.query.all()

    if os.path.exists('subscribers.txt'):
        with open('subscribers.txt', 'r') as f:
            subscribers = [line.strip() for line in f.readlines() if line.strip()]
    else:
        subscribers = []

    student_applications = []  # Placeholder: Replace with query from model if defined

    return render_template('admin_dashboard.html', blogs=blogs, messages=messages, users=users, subscribers=subscribers, student_applications=student_applications)

@app.route('/admin/create-blog', methods=['GET', 'POST'])
@login_required
def create_blog():
    if current_user.role != 'admin':
        flash('Unauthorized')
        return redirect(url_for('home'))
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        slug = title.lower().replace(' ', '-')
        with open(f'content/blogs/{slug}.md', 'w', encoding='utf-8') as f:
            f.write(content)
        flash('Blog created!')
        return redirect(url_for('admin_dashboard'))
    return render_template('create_blog.html')

@app.route('/admin/edit-blog/<slug>', methods=['GET', 'POST'])
@login_required
def edit_blog(slug):
    if current_user.role != 'admin':
        flash('Unauthorized')
        return redirect(url_for('home'))
    path = f'content/blogs/{slug}.md'
    if not os.path.exists(path):
        abort(404)
    if request.method == 'POST':
        content = request.form['content']
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        flash('Blog updated.')
        return redirect(url_for('admin_dashboard'))
    with open(path, 'r', encoding='utf-8') as f:
        current_content = f.read()
    return render_template('edit_blog.html', slug=slug, content=current_content)

@app.route('/admin/delete-blog/<slug>')
@login_required
def delete_blog(slug):
    if current_user.role != 'admin':
        flash('Unauthorized')
        return redirect(url_for('home'))
    path = f'content/blogs/{slug}.md'
    if os.path.exists(path):
        os.remove(path)
        flash('Blog deleted.')
    else:
        flash('Blog not found.')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
