from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# App and database configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = '61030dacbc95ed5d0e86a87fda8166b1b58bf787e14170dab2dc52df3a1f84d0'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://uinvwsoqhrrdir:61030dacbc95ed5d0e86a87fda8166b1b58bf787e14170dab2dc52df3a1f84d0@ec2-52-5-167-89.compute-1.amazonaws.com:5432/d192656rsmtm0u'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(255), nullable=False)
    user_email = db.Column(db.String(30), unique=True, nullable=False)
    user_password = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.user_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.user_password, password)

    # Override get_id to use user_id as the identifier for Flask-Login
    def get_id(self):
        return str(self.user_id)  # Return a string value, Flask-Login expects the id to be unicode or string
class Alert(db.Model):
    __tablename__ = 'alerts'

    alert_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    pi_id = db.Column(db.Integer, db.ForeignKey('pestpis.pi_id'))
    alert_type = db.Column(db.String(20))
    alert_date = db.Column(db.DateTime, default=datetime.utcnow)
    alert_isactive = db.Column(db.Boolean)

    def __repr__(self):
        return f"<Alert {self.alert_id}, Type: {self.alert_type}, Date: {self.alert_date}, Active: {self.alert_isactive}>"
# Load user by ID
class PestPi(db.Model):
    __tablename__ = 'pestpis'

    pi_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    pi_ipmain = db.Column(db.String(20))
    pi_location = db.Column(db.String(20))
    pi_ip = db.Column(db.String(20), unique=True)
    pi_status = db.Column(db.String(10))

    def __repr__(self):
        return f'<PestPi {self.pi_id} located at {self.pi_location}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        user_exists = User.query.filter_by(user_email=email).first()

        if user_exists:
            flash('Email already exists.')
            return redirect(url_for('register'))

        new_user = User(user_name=name, user_email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Your account has been created, you can now log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()  # This function comes from Flask-Login and handles the session cleanup
    print("EHLO MATE YA LOGGED OFF")
    return redirect(url_for('login'))  # Assuming you have a route named 'login' for your login page
@app.route('/')
@login_required
def dashboard():

    return render_template('dashboard.html', name=current_user.user_name)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(user_email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return jsonify(success=True), 200  # Or directly return a redirect from server
        else:
            flash('Invalid email or password')
            return jsonify(success=False, message="Invalid email or password"), 401

    return render_template('login.html')



from flask import jsonify


@app.route('/api/alerts')
def get_alerts():
    # Example of fetching counts; adjust based on your actual database schema
    iguana_count = Alert.query.filter_by(alert_type='iguana', alert_isactive=True).count()
    rodent_count = Alert.query.filter_by(alert_type='rodent', alert_isactive=True).count()
    boa_count = Alert.query.filter_by(alert_type='boa', alert_isactive=True).count()
    print(iguana_count, rodent_count, boa_count)
    return jsonify({
        'iguana': iguana_count,
        'rodent': rodent_count,
        'boa': boa_count
    })


@app.route('/update_email', methods=['POST'])
def update_email():
    # Get user_id from session or request, validate new email, then update in the database
    return jsonify(success=True)


@app.route('/configure_pestpi', methods=['POST'])
def configure_pestpi():
    if not request.json:
        return jsonify({'error': 'Missing JSON data'}), 400

    # Extract data from JSON
    pi_ipmain = request.json.get('pi_ipmain')
    pi_location = request.json.get('pi_location')
    pi_ip = request.json.get('pi_ip')

    # Assuming you have access to the user_id here
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    # Find existing or create new PestPi
    pestpi = PestPi.query.filter_by(pi_ip=pi_ip).first()
    if pestpi:
        pestpi.pi_ipmain = pi_ipmain
        pestpi.pi_location = pi_location
    else:
        pestpi = PestPi(user_id=user_id, pi_ipmain=pi_ipmain, pi_location=pi_location, pi_ip=pi_ip)
        db.session.add(pestpi)

    db.session.commit()
class MainPest(db.Model):
    __tablename__ = 'mainpests'

    main_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    main_ip = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f'<MainPest {self.main_id}, User ID: {self.user_id}, Main IP: {self.main_ip}>'

@app.route('/set_main_pestpi', methods=['POST'])
def set_main_pestpi():
    if not request.json or 'main_ip' not in request.json:
        return jsonify({'error': 'Missing main IP data'}), 400

    main_ip = request.json['main_ip']
    # Add your logic here to update the main IP in your database
    try:
        # Assuming MainPest model exists and is correctly linked to user_id
        user_id = get_current_user_id()  # Make sure this function exists and correctly fetches the user ID
        main_pest = MainPest.query.filter_by(user_id=user_id).first()
        if main_pest:
            main_pest.main_ip = main_ip
        else:
            # Create new MainPest if not exists
            new_main_pest = MainPest(user_id=user_id, main_ip=main_ip)
            db.session.add(new_main_pest)
        db.session.commit()
        return jsonify(success=True, message='Main PestPi IP updated successfully')
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

# Run the app
# User loader setup
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)
def get_current_user_id():
    if current_user.is_authenticated:
        return current_user.user_id  # Assuming your user model has a 'user_id' attribute
    return None

@app.route('/api/pestpis')
def get_pestpis():
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({'error': 'User not authenticated'}), 401

    pestpis = PestPi.query.filter_by(user_id=user_id).all()
    pestpi_data = [{'pi_id': pi.pi_id, 'pi_ip': pi.pi_ip, 'pi_location': pi.pi_location} for pi in pestpis]
    return jsonify(pestpi_data)


@app.route('/change_password', methods=['POST'])
@login_required  # Ensure that the user is logged in before allowing password changes
def change_password():
    data = request.get_json()  # Get the data sent with the POST request
    new_password = data['password']  # Extract the new password from the data

    try:
        # Update the password using the set_password method of the current_user, which is already loaded by Flask-Login
        current_user.set_password(new_password)
        db.session.commit()  # Commit the changes to the database
        return jsonify({'success': True, 'message': 'Password updated successfully'}), 200
    except Exception as e:
        print(e)  # For debugging purposes, you might want to log this somewhere in production
        return jsonify({'success': False, 'message': 'Failed to update the password'}), 500

if __name__ == '__main__':
    db.create_all()  # Create database tables at first run
    app.run(debug=True)
