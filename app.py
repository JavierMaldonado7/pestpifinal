import base64
import io
from datetime import datetime
from dateutil.relativedelta import relativedelta

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func, extract, LargeBinary

# App and database configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'bc565cc08ffecbeeac4ebda9e3362a43eb6b28031322c93304b87bb71a4314d0'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://vevnxnnnehlhcr:bc565cc08ffecbeeac4ebda9e3362a43eb6b28031322c93304b87bb71a4314d0@ec2-52-73-67-148.compute-1.amazonaws.com:5432/d12fhtfr8lc1ks'
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

    def get_id(self):
        return str(self.user_id)
class Alert(db.Model):
    __tablename__ = 'alerts'

    alert_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    pi_id = db.Column(db.Integer, db.ForeignKey('pestpis.pi_id'))
    alert_type = db.Column(db.String(20))
    alert_date = db.Column(db.DateTime, default=datetime.utcnow)
    alert_isactive = db.Column(db.Boolean)
    image = db.Column(LargeBinary)

    def serialize(self):
        return {
            'alert_id': self.alert_id,
            'user_id': self.user_id,
            'pi_id': self.pi_id,
            'alert_type': self.alert_type,
            'alert_date': self.alert_date.isoformat(),  # Or format as needed
            'alert_isactive': self.alert_isactive,
            'alert_location': get_pi_location(self.pi_id)  # Assuming you have a function to get location
        }
    def __repr__(self):
        return f"<Alert {self.alert_id}, Type: {self.alert_type}, Date: {self.alert_date}, Active: {self.alert_isactive}>"

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
    logout_user()
    return redirect(url_for('login'))
@app.route('/')
@login_required
def dashboard():

    return render_template('dashboard.html', name=current_user.user_name)

def calculate_date_range(filter_key):
    current_time = datetime.utcnow()
    if filter_key == 'today':
        start_date = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
    elif filter_key == 'this_week':
        start_date = current_time - timedelta(days=current_time.weekday())
        end_date = start_date + timedelta(weeks=1)
    elif filter_key == 'this_month':
        start_date = current_time.replace(day=1)
        end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)
    return start_date, end_date

def fetch_stats(timeframe):
    now = datetime.utcnow()
    query = Alert.query.with_entities(Alert.alert_type, func.count(Alert.alert_type).label('count'))
    if timeframe == 'today':
        query = query.filter(func.date(Alert.alert_date) == func.date(now))
    elif timeframe == 'weekly':
        week_ago = now - timedelta(days=7)
        query = query.filter(Alert.alert_date >= week_ago)
    elif timeframe == 'monthly':
        query = query.filter(extract('year', Alert.alert_date) == now.year,
                             extract('month', Alert.alert_date) == now.month)
    elif timeframe == 'yearly':
        query = query.filter(extract('year', Alert.alert_date) == now.year)
    return [{'type': stat.alert_type, 'count': stat.count} for stat in query.group_by(Alert.alert_type).all()]

@app.route('/api/filter')
def get_filt():
    alert_type = request.args.get('type', 'all')
    date_filter = request.args.get('date', 'all')
    location_filter = request.args.get('location', 'all')

    print(f"Received filters - Type: {alert_type}, Date: {date_filter}, Location: {location_filter}")

    query = Alert.query.filter(Alert.alert_isactive == True)

    if alert_type != 'all':
        query = query.filter_by(alert_type=alert_type)

    if date_filter != 'all':
        start_date, end_date = calculate_date_range(date_filter)
        query = query.filter(Alert.alert_date >= start_date, Alert.alert_date < end_date)

    if location_filter != 'all':
        query = query.join(PestPi, Alert.pi_id == PestPi.pi_id).filter(PestPi.pi_location == location_filter)

    results = query.all()
    print(f"Query executed: {query}")  # SQLAlchemy will show the query being run
    print(f"Number of results: {len(results)}")

    alerts = [{
        'alert_id': alert.alert_id,
        'alert_type': alert.alert_type,
        'alert_date': alert.alert_date.strftime('%Y-%m-%d %H:%M'),
        'alert_location': get_pi_location(alert.pi_id)  # Double-check this function too
    } for alert in results]

    return jsonify(alerts)




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
            return jsonify(success=True), 200
        else:
            flash('Invalid email or password')
            return jsonify(success=False, message="Invalid email or password"), 401

    return render_template('login.html')

@app.route('/api/locations', methods=['GET'])
@login_required
def get_locations():
    locations = PestPi.query.with_entities(PestPi.pi_location).distinct()
    locations = [location.pi_location for location in locations]
    return jsonify(locations)

@app.route('/api/stats/total_alerts')
@login_required
def total_alerts():
    # Count only alerts belonging to the current user
    total = Alert.query.filter_by(user_id=current_user.user_id).count()
    return jsonify({'total_alerts': total})
@app.route('/api/stats/alert_status')
def alert_status():

    active = Alert.query.filter_by(alert_isactive=True,user_id=current_user.user_id).count()
    resolved = Alert.query.filter_by(alert_isactive=False,user_id=current_user.user_id).count()
    return jsonify({'active': active, 'resolved': resolved})
@app.route('/api/stats/alerts_by_type')
@login_required
def alerts_by_type():
    user_id = current_user.user_id  # Retrieve the current user's ID
    stats = db.session.query(
        Alert.alert_type,
        func.count(Alert.alert_type).label('count')
    ).filter(Alert.user_id == user_id).group_by(Alert.alert_type).all()  # Filter by user_id and group by alert type

    return jsonify({atype: count for atype, count in stats})

from sqlalchemy import  cast, Date

@app.route('/api/stats/alerts_over_time')
@login_required
def alerts_over_time():
    user_id = get_current_user_id()  # Get the current user's ID
    # Fetching data from the database, grouped by date, filtered by the current user
    stats = db.session.query(
        cast(Alert.alert_date, Date).label('date'),  # Ensure the date is treated as a Date object without time
        func.count('*').label('count')
    ).filter(Alert.user_id == user_id).group_by('date').order_by('date').all()

    # Converting data to a serializable format
    result = {date.strftime("%Y-%m-%d"): count for date, count in stats}  # Format date as string "YYYY-MM-DD"

    return jsonify(result)
@app.route('/api/location_stats')
@login_required
def get_location_stats():
    user_id = current_user.user_id  # Get the current user's ID
    location_filter = request.args.get('location', 'most_frequent')
    time_filter = request.args.get('time', 'all_time')

    # Calculate date range based on the time filter
    now = datetime.now()
    if time_filter == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif time_filter == 'this_week':
        start_date = now - timedelta(days=now.weekday())
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif time_filter == 'this_month':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(day=28, hour=23, minute=59, second=59, microsecond=999999) + timedelta(days=4)  # Go to the end of the month
        end_date = end_date - timedelta(days=end_date.day)
    elif time_filter == 'this_year':
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
    else:
        start_date = None
        end_date = None

    try:
        # Construct the base query
        query = db.session.query(
            PestPi.pi_location,
            func.count(Alert.alert_id).label('count')
        ).join(Alert, PestPi.pi_id == Alert.pi_id).filter(Alert.user_id == user_id)

        # Apply time filter if specified
        if start_date and end_date:
            query = query.filter(Alert.alert_date >= start_date, Alert.alert_date <= end_date)

        # Apply location filter
        if location_filter != 'most_frequent':
            query = query.filter(PestPi.pi_location == location_filter)

        # Finalize the query
        query = query.group_by(PestPi.pi_location)
        if location_filter == 'most_frequent':
            query = query.order_by(func.count(Alert.alert_id).desc()).limit(5)

        stats = query.all()

        return jsonify([{'location': stat[0], 'count': stat[1]} for stat in stats])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pi_location/<int:pi_id>')
def get_pi_location(pi_id):
    pi = PestPi.query.filter_by(pi_id=pi_id).first()
    if pi:
        return pi.pi_location
    else:
        return jsonify({'error': 'Pi not found'}), 404


@app.route('/api/active_alerts')
@login_required
def active_alerts():
    # Fetch only active alerts related to the logged-in user
    alerts = Alert.query.filter_by(user_id=current_user.user_id, alert_isactive=True).order_by(Alert.alert_date.desc()).all()
    alerts_data = [{
        'alert_id': alert.alert_id,
        'alert_type': alert.alert_type,
        'alert_date': alert.alert_date.strftime("%Y-%m-%d  %H:%M"),
        'alert_location': get_pi_location(alert.pi_id)
    } for alert in alerts]

    return jsonify(alerts_data), 200

@app.route('/api/alerts')
@login_required
def get_alerts():
    # Only fetch alerts for the current logged-in user
    iguana_count = Alert.query.filter_by(user_id=current_user.user_id, alert_type='Iguana', alert_isactive=True).count()
    rodent_count = Alert.query.filter_by(user_id=current_user.user_id, alert_type='Rodent', alert_isactive=True).count()
    boa_count = Alert.query.filter_by(user_id=current_user.user_id, alert_type='Boa', alert_isactive=True).count()

    return jsonify({
        'iguana': iguana_count,
        'rodent': rodent_count,
        'boa': boa_count
    })

@app.route('/api/card_alerts')
def get_card():
    iguana_count = Alert.query.filter_by(alert_type='Iguana', alert_isactive=True,user_id=current_user.user_id).count()
    rodent_count = Alert.query.filter_by(alert_type='Rodent', alert_isactive=True,user_id=current_user.user_id).count()
    boa_count = Alert.query.filter_by(alert_type='Boa', alert_isactive=True,user_id=current_user.user_id).count()

    return jsonify({
        'iguana': iguana_count,
        'rodent': rodent_count,
        'boa': boa_count
    })


@app.route('/update_email', methods=['POST'])
def update_email():
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    data = request.get_json()
    new_email = data['email']
    if not new_email:
        return jsonify({'success': False, 'message': 'No email provided'}), 400

    try:
        current_user.user_email = new_email
        db.session.commit()
        return jsonify({'success': True, 'message': 'Email updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to update email'}), 500



@app.route('/configure_pestpi', methods=['POST'])
def configure_pestpi():
    if not request.json:
        return jsonify({'error': 'Missing JSON data'}), 400


    pi_ipmain = request.json.get('pi_ipmain')
    pi_location = request.json.get('pi_location')
    pi_ip = request.json.get('pi_ip')


    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

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

    try:
        user_id = get_current_user_id()
        main_pest = MainPest.query.filter_by(user_id=user_id).first()
        if main_pest:
            main_pest.main_ip = main_ip
        else:

            new_main_pest = MainPest(user_id=user_id, main_ip=main_ip)
            db.session.add(new_main_pest)
        db.session.commit()
        return jsonify(success=True, message='Main PestPi IP updated successfully')
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)
def get_current_user_id():
    if current_user.is_authenticated:
        return current_user.user_id
    return None

@app.route('/api/pestpis')
def get_pestpis():
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({'error': 'User not authenticated'}), 401

    pestpis = PestPi.query.filter_by(user_id=user_id).all()
    pestpi_data = [{'pi_id': pi.pi_id, 'pi_ip': pi.pi_ip, 'pi_location': pi.pi_location} for pi in pestpis]
    return jsonify(pestpi_data)

from datetime import datetime, timedelta

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json()
    new_password = data['password']

    try:
        current_user.set_password(new_password)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Password updated successfully'}), 200
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': 'Failed to update the password'}), 500

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    timeframe = request.args.get('timeframe', 'daily')
    stats_data = fetch_stats(timeframe)
    return jsonify(stats_data)

from flask import jsonify

@app.route('/api/del_alert', methods=['POST'])
@login_required
def del_alert():
    try:

        data = request.get_json()
        alert_id = data.get('alert_id')
        alert = Alert.query.filter_by(alert_id=alert_id, user_id=current_user.user_id).first()

        if alert:
            db.session.delete(alert)
            db.session.commit()
            return jsonify({"success": True, "message": "Alert removed successfully."}), 200
        else:
            return jsonify({"success": False, "message": "Alert not found or you do not have permission to remove it."}), 404
    except Exception as e:
        print(f"Error removing alert: {e}")
        return jsonify({"success": False, "message": "An error occurred while removing the alert."}), 500
@app.route('/api/remove_alert', methods=['POST'])
@login_required
def remove_alert():
    try:
        data = request.get_json()
        alert_id = data.get('alert_id')
        alert = Alert.query.filter_by(alert_id=alert_id, user_id=current_user.user_id).first()

        if alert:
            # Correctly set the alert to inactive
            alert.alert_isactive = False  # Use the correct attribute name
            db.session.commit()
            return jsonify({"success": True, "message": "Alert set to inactive successfully."}), 200
        else:
            return jsonify({"success": False, "message": "Alert not found or you do not have permission to modify it."}), 404
    except Exception as e:
        print(f"Error setting alert to inactive: {e}")
        return jsonify({"success": False, "message": "An error occurred while updating the alert."}), 500

from flask import send_file

@app.route('/api/image/<int:alert_id>')
@login_required
def get_image(alert_id):
    alert = Alert.query.filter_by(alert_id=alert_id, user_id=current_user.user_id).first()
    if alert and alert.image:
        return send_file(
            io.BytesIO(alert.image),
            mimetype='image/jpeg'
        )
    return jsonify({'error': 'Image not found or access denied'}), 404

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
