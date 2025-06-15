from models import db, User
from app import app  # Adjust this import if your app is named differently

with app.app_context():
    user = User.query.filter_by(email='arunreghunathan953@gmail.com').first()
    if user:
        user.role = 'admin'
        db.session.commit()
        print(f"Updated {user.email} to admin.")
    else:
        print("User not found.")
