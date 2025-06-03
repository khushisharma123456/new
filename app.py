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
    survey_completed = db.Column(db.Boolean, default=False)
    cycle_length = db.Column(db.Integer, default=28)  # Added to store user's cycle length
    period_length = db.Column(db.Integer, default=5)  # Added to store user's period length

    # Relationship to track history
    entries = db.relationship('PainEntry', backref='user', lazy=True)

class PainEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    pain_level = db.Column(db.String(20))
    flow_level = db.Column(db.String(20))
    mood = db.Column(db.String(20))
    symptoms = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)

class SurveyResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Survey questions
    q1_feel_off = db.Column(db.String(20))
    q2_skin_changes = db.Column(db.String(20))
    q3_cravings_shift = db.Column(db.String(20))
    q4_energy_changes = db.Column(db.String(20))
    q5_workout_variation = db.Column(db.String(20))
    q6_cycle_length = db.Column(db.Integer)
    q7_period_length = db.Column(db.Integer)
    q8_PMS = db.Column(db.String(20))
    q9_health_conditions = db.Column(db.String(20))
    
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
        is_new_signup = 'is_new_signup' in request.form  # Check for new signup

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(full_name=full_name, email=email, password=hashed_password, survey_completed=False)

        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Log the user in automatically
            session['user_id'] = new_user.id
            session['user_name'] = new_user.full_name
            
            # Redirect to survey for new signups, dashboard otherwise
            if is_new_signup:
                flash('Account created! Please complete our quick survey.', 'success')
                return redirect(url_for('survey'))
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('Email already registered!', 'danger')
            return redirect(url_for('signup'))

    return render_template('signup.html')

@app.route('/survey', methods=['GET', 'POST'])
def survey():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user:
        flash('User not found!', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            # Save survey responses
            new_response = SurveyResponse(
                user_id=session['user_id'],
                q1_feel_off=request.form.get('q1'),
                q2_skin_changes=request.form.get('q2'),
                q3_cravings_shift=request.form.get('q3'),
                q4_energy_changes=request.form.get('q4'),
                q5_workout_variation=request.form.get('q5'),
                q6_cycle_length=request.form.get('cycle_length', type=int),
                q7_period_length=request.form.get('period_length', type=int),
                q8_PMS=request.form.get('q8'),
                q9_health_conditions=request.form.get('q9')
            )

            # Update user's cycle and period length
            user.cycle_length = request.form.get('cycle_length', type=int)
            user.period_length = request.form.get('period_length', type=int)
            user.survey_completed = True

            db.session.add(new_response)
            db.session.commit()
            flash('Thank you for completing the survey!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error saving survey responses. Please try again.', 'danger')

    if user.survey_completed:
        flash('You have already completed the survey!', 'info')
        return redirect(url_for('dashboard'))

    return render_template('survey.html', user_name=session['user_name'])


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
        
    user = User.query.get(session['user_id'])
    if not user.survey_completed:
        flash('Please complete the survey first!', 'warning')
        return redirect(url_for('survey'))
        
    return render_template('dashboard.html', user_name=session['user_name'])
# Period Tracker Page (Only for logged-in users)
pain_mapping = {'No Pain': 0, 'Mild': 3, 'Moderate': 5, 'Severe': 10}
flow_mapping = {'None': 0, 'Light': 2, 'Medium': 5, 'Heavy': 8}

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, timedelta
import os
import json

try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "menstrualcyclelen.json")
    print("Loading JSON from:", json_path)

    with open(json_path, "r") as f:
        data = json.load(f)
except FileNotFoundError as e:
    print("File not found:", e)
    data = {}  # Or maybe you want to crash intentionally with raise e
except Exception as e:
    print("Unexpected error loading JSON:", e)
    data = {}


# ------------------------ Helper: Predict Cycle ------------------------
def predict_cycle(start_date_str, cycle_length):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    next_period = start_date + timedelta(days=cycle_length)
    ovulation_start = next_period - timedelta(days=14)
    ovulation_end = ovulation_start + timedelta(days=5)

    return {
        "next_period": next_period.strftime("%Y-%m-%d"),
        "ovulation_window": [
            ovulation_start.strftime("%Y-%m-%d"),
            ovulation_end.strftime("%Y-%m-%d")
        ]
    }

# ------------------------ Main Route ------------------------
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta


@app.route('/period_tracker', methods=['GET', 'POST'])
def period_tracker():
    if request.method == 'POST':
        start_date_str = request.form.get('start_date')  # This should now be a valid string
        if not start_date_str:
            return "Start date is required", 400

        # Convert string to datetime object
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')

        # Get other form data
        flow = request.form.get('flow')
        symptoms = request.form.getlist('symptoms')
        emotions = request.form.getlist('emotions')
        notes = request.form.get('notes')

        # Calculate next period date (example logic: 28-day cycle)
        next_period_date = start_date + timedelta(days=28)

        return render_template('tracker_result.html',
                               start_date=start_date_str,
                               next_period_date=next_period_date.strftime('%Y-%m-%d'),
                               flow=flow,
                               symptoms=symptoms,
                               emotions=emotions,
                               notes=notes)

    return render_template('period_tracker.html')


# ------------------------ Separate API Route (Optional) ------------------------
@app.route('/predict_cycle', methods=['POST'])
def cycle_predict():
    start_date = request.form['start_date']
    cycle_length = int(request.form['cycle_length'])
    prediction = predict_cycle(start_date, cycle_length)
    return jsonify(prediction)


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
