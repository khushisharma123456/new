from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from urllib.parse import unquote
import os
import json
import requests
from urllib.parse import urlencode

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Spotify configuration
SPOTIFY_CLIENT_ID = '6b770d2f043948dc9515d3a5f65a5113'
SPOTIFY_CLIENT_SECRET = 'bbf02678958948eda30ff6bc0e616058'
SPOTIFY_REDIRECT_URI = 'http://localhost:5000/callback'
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'

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


class SurveyResponse(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    q1_age = db.Column(db.Integer)
    q2_last_period = db.Column(db.Date)
    q3_period_duration = db.Column(db.String(30))
    q4_cycle_length = db.Column(db.String(30))
    q5_period_regularity = db.Column(db.String(30))
    q6_hair_growth = db.Column(db.String(10))
    q7_acne = db.Column(db.String(10))
    q8_hair_thinning = db.Column(db.String(10))
    q9_weight_gain = db.Column(db.String(30))
    q10_sugar_craving = db.Column(db.String(10))
    q11_family_history = db.Column(db.String(30))
    q12_fertility = db.Column(db.String(30))
    q13_mood_swings = db.Column(db.String(30))

    
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
            new_response = SurveyResponse(
                user_id=session['user_id'],
                q1_age=request.form.get('q1', type=int),
                q2_last_period=datetime.strptime(request.form.get('q2'), '%Y-%m-%d').date(),
                q3_period_duration=request.form.get('q3'),  # Period duration select has same `name="q2"` — needs correction!
                q4_cycle_length=request.form.get('q4'),
                q5_period_regularity=request.form.get('q5'),
                q6_hair_growth=request.form.get('q6'),
                q7_acne=request.form.get('q7'),
                q8_hair_thinning=request.form.get('q8'),
                q9_weight_gain=request.form.get('q9'),
                q10_sugar_craving=request.form.get('q10'),
                q11_family_history=request.form.get('q11'),
                q12_fertility=request.form.get('q12'),
                q13_mood_swings=request.form.get('q13')
            )

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

    # ⬇️ Fetch latest survey response
    survey = SurveyResponse.query.filter_by(user_id=user.id).order_by(SurveyResponse.timestamp.desc()).first()

    if not survey or not survey.q2_last_period:
        flash('Survey data is missing or incomplete.', 'warning')
        return redirect(url_for('survey'))

    # Calculate cycle day and phase
    today = datetime.utcnow().date()
    days_since_period = (today - survey.q2_last_period).days
    current_day = (days_since_period % user.cycle_length) + 1 if days_since_period >= 0 else 0

    if current_day <= user.period_length:
        current_phase = "Menstrual"
    elif current_day <= (user.cycle_length - 14):
        current_phase = "Follicular"
    elif current_day <= (user.cycle_length - 9):
        current_phase = "Ovulation"
    else:
        current_phase = "Luteal"

    return render_template(
        'index.html',
        user_name=session['user_name'],
        current_day=current_day,
        current_phase=current_phase,
        cycle_length=user.cycle_length,
        period_length=user.period_length
    )

    
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

@app.route('/consultation')
def consultation():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('consultation.html', user_name=session['user_name'])

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

#=====================================================================================
def load_recipes():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, 'data', 'recipes.json')
        
        with open(json_path) as f:
            data = json.load(f)
            return {recipe['title'].lower(): recipe for recipe in data['recipes']}
    except Exception as e:
        print(f"Error loading recipes: {str(e)}")
        return {}

recipes = load_recipes()

@app.route('/remedy/<path:remedy_name>')
def remedy_details(remedy_name):
    print(f"\n\n=== DEBUG: Received request for: {remedy_name} ===")  # Check terminal
    decoded_name = unquote(remedy_name).lower()
    print(f"Decoded name: {decoded_name}")
    
    recipe = recipes.get(decoded_name)
    if not recipe:
        recipe = recipes.get(remedy_name.replace('-', ' ').lower())
    
    if not recipe:
        print("Recipe not found!")
        abort(404)
    
    print(f"Found recipe: {recipe['title']}")  # Verify match
    return render_template('remedy.html', remedy=recipe)

@app.route('/callback')
def spotify_callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})
    
    if 'code' in request.args:
        code = request.args['code']
        
        # Exchange code for access token
        auth_response = requests.post(SPOTIFY_TOKEN_URL, {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': SPOTIFY_REDIRECT_URI,
            'client_id': SPOTIFY_CLIENT_ID,
            'client_secret': SPOTIFY_CLIENT_SECRET,
        })
        
        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            access_token = auth_data['access_token']
            refresh_token = auth_data['refresh_token']
            
            # Store tokens in session
            session['spotify_access_token'] = access_token
            session['spotify_refresh_token'] = refresh_token
            
            # Redirect back to the main page
            return redirect(url_for('index'))
        else:
            return jsonify({"error": "Failed to get access token"})
    
    return jsonify({"error": "No code provided"})

@app.route('/refresh_token')
def refresh_token():
    if 'spotify_refresh_token' not in session:
        return jsonify({"error": "No refresh token"})
    
    refresh_response = requests.post(SPOTIFY_TOKEN_URL, {
        'grant_type': 'refresh_token',
        'refresh_token': session['spotify_refresh_token'],
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET,
    })
    
    if refresh_response.status_code == 200:
        refresh_data = refresh_response.json()
        session['spotify_access_token'] = refresh_data['access_token']
        return jsonify({"access_token": refresh_data['access_token']})
    else:
        return jsonify({"error": "Failed to refresh token"})

            
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
