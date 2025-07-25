from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from urllib.parse import unquote
import os
import json
import requests
from urllib.parse import urlencode
import logging

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session management
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PREFERRED_URL_SCHEME'] = 'https'

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)  # Added phone_number field
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

@app.route('/logout', methods=['POST'])
def logout():
    try:
        # Clear the session
        session.clear()
        # Return success response
        return jsonify({
            'success': True,
            'message': 'Logged out successfully',
            'redirect': url_for('index')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error during logout'
        }), 500

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

@app.route('/spotify-callback')
def spotify_callback():
    try:
        code = request.args.get('code')
        if not code:
            logger.error("No code received from Spotify")
            return redirect(url_for('index'))
        
        # Exchange code for access token
        token_url = 'https://accounts.spotify.com/api/token'
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': SPOTIFY_REDIRECT_URI,
            'client_id': SPOTIFY_CLIENT_ID,
            'client_secret': SPOTIFY_CLIENT_SECRET
        }
        
        logger.debug(f"Attempting to exchange code for token with data: {token_data}")
        response = requests.post(token_url, data=token_data)
        
        if response.status_code == 200:
            token_info = response.json()
            session['spotify_access_token'] = token_info['access_token']
            session['spotify_refresh_token'] = token_info['refresh_token']
            session['token_expires_at'] = datetime.now() + timedelta(seconds=token_info['expires_in'])
            
            logger.info("Successfully obtained Spotify access token")
            return '''
            <html>
                <body>
                    <script>
                        localStorage.setItem('spotify_access_token', '{}');
                        window.close();
                    </script>
                </body>
            </html>
            '''.format(token_info['access_token'])
        else:
            logger.error(f"Failed to get access token. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return redirect(url_for('index'))
            
    except Exception as e:
        logger.error(f"Error in spotify_callback: {str(e)}")
        return redirect(url_for('index'))

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

            


# Spotify API credentials
SPOTIFY_CLIENT_ID = '6b770d2f043948dc9515d3a5f65a5113'  # Your Spotify Client ID
SPOTIFY_CLIENT_SECRET = 'bbf02678958948eda30ff6bc0e616058'  # Your Spotify Client Secret
SPOTIFY_REDIRECT_URI = 'https://YOUR_NGROK_URL.ngrok.io/spotify-callback'  # Replace YOUR_NGROK_URL with your actual ngrok subdomain

class Mood(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mood = db.Column(db.String(50), nullable=False)
    intensity = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationship with User
    user = db.relationship('User', backref=db.backref('moods', lazy=True))

    def __repr__(self):
        return f'<Mood {self.mood} {self.intensity} {self.date}>'

@app.route('/api/save_mood', methods=['POST'])
@app.route('/dashboard/save_mood', methods=['POST'])
def save_mood():
    try:
        # Log the request details
        app.logger.info(f"Request method: {request.method}")
        app.logger.info(f"Request headers: {dict(request.headers)}")
        app.logger.info(f"Request data: {request.get_data()}")
        
        # Ensure we're returning JSON
        if not request.is_json:
            app.logger.error("Request is not JSON")
            return jsonify({'error': 'Request must be JSON'}), 400

        app.logger.info(f"Session contents: {dict(session)}")  # Log session contents
        
        if 'user_id' not in session:
            app.logger.error("User not logged in - no user_id in session")
            return jsonify({'error': 'Please log in first to save your mood'}), 401

        data = request.get_json()
        app.logger.info(f"Received data: {data}")  # Log the received data
        
        if not data:
            app.logger.error("No JSON data received")
            return jsonify({'error': 'No data received'}), 400
        
        mood = data.get('mood')
        intensity = data.get('intensity')
        date = data.get('date')
        
        app.logger.info(f"Parsed data: mood={mood}, intensity={intensity}, date={date}")
        
        if not all([mood, intensity, date]):
            missing_fields = []
            if not mood: missing_fields.append('mood')
            if not intensity: missing_fields.append('intensity')
            if not date: missing_fields.append('date')
            app.logger.error(f"Missing required mood data: {', '.join(missing_fields)}")
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

        try:
            intensity = int(intensity)  # Ensure intensity is an integer
            if not (1 <= intensity <= 5):
                app.logger.error(f"Intensity out of range: {intensity}")
                return jsonify({'error': 'Intensity must be between 1 and 5'}), 400
        except ValueError:
            app.logger.error(f"Invalid intensity value: {intensity}")
            return jsonify({'error': 'Invalid intensity value'}), 400

        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            app.logger.error(f"Invalid date format: {date}")
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        new_mood = Mood(
            user_id=session['user_id'],
            mood=mood,
            intensity=intensity,
            date=date_obj
        )
        
        app.logger.info(f"Creating new mood entry: {new_mood}")
        db.session.add(new_mood)
        db.session.commit()
        
        app.logger.info(f"Successfully saved mood: {new_mood.id}")
        return jsonify({
            'message': 'Mood saved successfully',
            'mood_id': new_mood.id,
            'mood': mood,
            'intensity': intensity,
            'date': date
        })
    except Exception as e:
        app.logger.error(f"Error saving mood: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/get_mood_history')
def get_mood_history():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'User not logged in'}), 401

        moods = Mood.query.filter_by(user_id=session['user_id']).order_by(Mood.date.desc()).all()
        app.logger.info(f"Retrieved {len(moods)} moods from database")
        
        mood_data = [{
            'mood': mood.mood,
            'intensity': mood.intensity,
            'date': mood.date.strftime('%Y-%m-%d')
        } for mood in moods]
        
        app.logger.info(f"Mood data: {mood_data}")
        return jsonify(mood_data)
    except Exception as e:
        app.logger.error(f"Error retrieving mood history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/mood')
def mood_history():
    return render_template('mood.html')

@app.route('/api/change-password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'}), 401
    
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'success': False, 'message': 'Please provide both current and new password'}), 400
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Verify current password
    if not check_password_hash(user.password, current_password):
        return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400
    
    # Validate new password
    if len(new_password) < 8:
        return jsonify({'success': False, 'message': 'New password must be at least 8 characters long'}), 400
    
    # Check for at least one number and one special character
    if not any(char.isdigit() for char in new_password):
        return jsonify({'success': False, 'message': 'New password must contain at least one number'}), 400
    
    if not any(char in '@$!%*#?&' for char in new_password):
        return jsonify({'success': False, 'message': 'New password must contain at least one special character (@$!%*#?&)'}), 400
    
    try:
        # Update password
        user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
        db.session.commit()
        return jsonify({'success': True, 'message': 'Password updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred while updating password'}), 500

@app.route('/api/update-profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'}), 401
    
    data = request.get_json()
    user = User.query.get(session['user_id'])
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    try:
        # Update user fields
        if 'first_name' in data and 'last_name' in data:
            user.full_name = f"{data['first_name']} {data['last_name']}"
        if 'phone_number' in data:
            user.phone_number = data['phone_number']
        if 'birth_date' in data:
            user.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
        
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': 'Profile updated successfully',
            'user': {
                'full_name': user.full_name,
                'phone_number': user.phone_number,
                'birth_date': user.birth_date.strftime('%Y-%m-%d') if user.birth_date else None
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred while updating profile'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)