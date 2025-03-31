from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    
    # Relationship to track history
    entries = db.relationship('PainEntry', backref='user', lazy=True)

class PainEntry(db.Model):  # Stores pain, flow, mood, symptoms in one table
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    pain_level = db.Column(db.String(20))  # No Pain, Mild, Moderate, Severe
    flow_level = db.Column(db.String(20))  # Light, Medium, Heavy
    mood = db.Column(db.String(20))  # Happy, Calm, Irritable, Emotional
    symptoms = db.Column(db.String(200))  # Store multiple symptoms as a comma-separated string
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)  # Store as comma-separated values
    instructions = db.Column(db.Text, nullable=False)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.full_name
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'danger')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(full_name=full_name, email=email, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))
        except:
            flash('Email already registered!', 'danger')

    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('dashboard.html', user_name=session['user_name'])

# Period Tracker Page (Only for logged-in users)
pain_mapping = {'No Pain': 0, 'Mild': 3, 'Moderate': 5, 'Severe': 10}
flow_mapping = {'None': 0, 'Light': 2, 'Medium': 5, 'Heavy': 8}

@app.route('/period-tracker', methods=['GET', 'POST'])
def period_tracker():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    user_id = session['user_id']

    if request.method == 'POST':
        flow = request.form.get('flow')
        pain = request.form.get('pain')
        mood = request.form.get('mood')
        symptoms = request.form.getlist('symptoms')  # Get list of selected checkboxes

        # Convert list to a comma-separated string for storage
        symptoms_str = ', '.join(symptoms) if symptoms else None

        new_entry = PainEntry(
            user_id=session['user_id'],
            flow_level=flow,  # Correct field name
            pain_level=pain,  # Correct field name
            mood=mood,
            symptoms=symptoms_str
        )

        db.session.add(new_entry)
        db.session.commit()

        flash('Your period tracking data has been saved!', 'success')
        return redirect(url_for('period_tracker'))  # Refresh page after submission

    entries = PainEntry.query.filter_by(user_id=user_id).order_by(PainEntry.date).all()

    # Convert categorical values to numerical values
    data = {
        "dates": [entry.date.strftime("%Y-%m-%d") for entry in entries],
        "pain_levels": [pain_mapping.get(entry.pain_level, 0) for entry in entries],
        "flow_levels": [flow_mapping.get(entry.flow_level, 0) for entry in entries],
        "moods": [entry.mood for entry in entries]  # Mood remains unchanged
    }

    return render_template('period-tracker.html', user_name=session['user_name'], data=data)

@app.route('/nutrition')
def nutrition():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('Nutrition.html')

@app.route('/train')
def train():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('train.html')

@app.route('/index')
def index():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('index (1).html')

@app.route('/about')
def about():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('about.html')

@app.route('/New-Pose')
def New_Pose():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('/New Pose.html')

@app.route('/recipe/<int:recipe_id>')
def recipe_page(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    ingredients = recipe.ingredients.split(',')
    instructions = recipe.instructions.split('.')
    return render_template('recipe.html', recipe=recipe, ingredients=ingredients, instructions=instructions)

@app.route('/yoga')
def yoga():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('yoga.html', user_name=session['user_name'])

@app.route('/admin')
def admin():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('admin.html', user_name=session['user_name'])

@app.route('/get-consultation')
def consultation():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('get-consultation.html', user_name=session['user_name'])

@app.route('/mood')
def mood():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('mood.html', user_name=session['user_name'])

@app.route('/beginner-yoga')
def beginner_yoga():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('beginner-yoga.html')

@app.route('/individual-practice')
def individual_practice():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('individual-practice.html')

@app.route('/regular-practice')
def regular_practice():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('regular-practice.html')

@app.route('/chatbot')
def chatbot():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('chatbot.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
