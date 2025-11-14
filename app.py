# =================================================================
# SafarSafe: Smart Tourist Safety App - Flask Backend MVP
# =================================================================
import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from sqlalchemy.dialects.postgresql import UUID
import uuid
from dotenv import load_dotenv
from functools import wraps
from geoalchemy2.types import Geography
from geoalchemy2.functions import ST_AsText

# 
print("==========================================")
print("--- RUNNING APP.PY ---")
print("==========================================")


# --- 1. INITIALIZATION -

load_dotenv()

app = Flask(__name__)
CORS(app)

# 
HARDCODED_DATABASE_URL = "postgresql://postgres:rQdeJc1F518ZfJx4@vwawdhhefdonbdwgzdrn.supabase.co:6543/postgres"

app.config['SQLALCHEMY_DATABASE_URI'] = HARDCODED_DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = "a_very_long_and_super_secret_string_for_your_hackathon_project_12345!"

print(f"DEBUG: ATTEMPTING TO CONNECT WITH: {app.config['SQLALCHEMY_DATABASE_URI']}")

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# --- 2. DATABASE MODELS (using SQLAlchemy) ---

class Tourist(db.Model):
    __tablename__ = 'Tourists'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fullName = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)

    def __init__(self, fullName, email, password):
        self.fullName = fullName
        self.email = email
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

class LocationHistory(db.Model):
    __tablename__ = 'LocationHistory'
    id = db.Column(db.BigInteger, primary_key=True)
    touristId = db.Column(UUID(as_uuid=True), db.ForeignKey('Tourists.id'), nullable=False)
    location = db.Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

# --- 3. API ROUTES ---

@app.route('/api/tourist/register', methods=['POST'])
def register_tourist():
    data = request.get_json()
    if not all(key in data for key in ['fullName', 'email', 'password']):
        return jsonify({"error": "Missing required fields"}), 400

    if Tourist.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already registered"}), 409

    try:
        new_tourist = Tourist(
            fullName=data['fullName'],
            email=data['email'],
            password=data['password']
        )
        db.session.add(new_tourist)
        db.session.commit()
        return jsonify({"message": "Registration successful", "touristId": new_tourist.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Registration failed", "details": str(e)}), 500

@app.route('/api/tourist/login', methods=['POST'])
def login_tourist():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    tourist = Tourist.query.filter_by(email=email).first()

    if tourist and bcrypt.check_password_hash(tourist.password, password):
        access_token = create_access_token(identity=str(tourist.id))
        return jsonify(message="Login successful", token=access_token), 200
    
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/tourist/profile', methods=['GET'])
@jwt_required()
def get_tourist_profile():
    tourist = Tourist.query.get(get_jwt_identity())
    if not tourist:
        return jsonify({"error": "Profile not found"}), 404

    return jsonify({"id": tourist.id, "fullName": tourist.fullName, "email": tourist.email}), 200

@app.route('/api/tourist/panic', methods=['POST'])
@jwt_required()
def trigger_panic():
    current_tourist_id = get_jwt_identity()
    data = request.get_json()
    if not all(key in data for key in ['latitude', 'longitude']):
        return jsonify({"error": "Location data is required"}), 400

    print(f"PANIC ALERT from tourist {current_tourist_id} at [{data['latitude']}, {data['longitude']}]")
    socketio.emit('new-panic-alert', {
        'touristId': current_tourist_id,
        'location': {'latitude': data['latitude'], 'longitude': data['longitude']},
        'timestamp': db.func.now().isoformat()
    })
    return jsonify({"message": "Panic alert sent successfully"}), 200

# --- 4. WEBSOCKET LOGIC ---

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')

@socketio.on('updateLocation')
def handle_location_update(data):
    if not all(key in data for key in ['touristId', 'latitude', 'longitude']):
        return print("Received incomplete location data. Ignoring.")

    print(f"Location update from {data['touristId']}: [{data['latitude']}, {data['longitude']}]")
    
    try:
        location_point = f"POINT({data['longitude']} {data['latitude']})"
        new_location = LocationHistory(touristId=data['touristId'], location=location_point)
        db.session.add(new_location)
        db.session.commit()
        print(f"Successfully saved location for tourist {data['touristId']}")
    except Exception as e:
        db.session.rollback()
        return print(f"Error saving location to database: {e}")

    socketio.emit('tourist-location-change', data)

# --- 5. SERVER STARTUP ---

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)

