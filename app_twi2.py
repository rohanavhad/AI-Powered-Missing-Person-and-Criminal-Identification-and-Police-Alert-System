from flask import Flask, render_template, request, redirect, url_for, Response, jsonify, session
import sqlite3
import face_recognition
import numpy as np
import cv2
import pickle
import threading
from datetime import datetime, timedelta
from twilio.rest import Client

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'

# Twilio Configuration
TWILIO_ACCOUNT_SID = ''
TWILIO_AUTH_TOKEN = ''
TWILIO_PHONE_NUMBER = ''

# Location-specific contact numbers
LOCATION_CONTACTS = {
    'location1': '+9100000113491',
    'location2': '+910000113491',
    'location3': '+910000113491'
}

# Notification settings
SMS_COOLDOWN = timedelta(minutes=5)
last_notification_times = {}

# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password'

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Store frames from different locations
client_frames = {}

def get_db_connection():
    return sqlite3.connect('record.db')

def send_sms_alert(name, category, location):
    """Send SMS alert to location-specific contact"""
    current_time = datetime.now()
    notification_key = f"{location}_{name}"
    
    # Check cooldown period
    if notification_key in last_notification_times:
        if current_time - last_notification_times[notification_key] < SMS_COOLDOWN:
            print(f"Skipping SMS for {name} at {location} - within cooldown period")
            return False
    
    if location in LOCATION_CONTACTS:
        try:
            message = (
                f"⚠️ ALERT at {location}:\n"
                f"Person Detected: {name}\n"
                f"Category: {category}\n"
                f"Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            twilio_client.messages.create(
                body=message,
                from_=TWILIO_PHONE_NUMBER,
                to=LOCATION_CONTACTS[location]
            )
            
            last_notification_times[notification_key] = current_time
            print(f"SMS alert sent to {location} contact for {name}")
            return True
        except Exception as e:
            print(f"Error sending SMS to {location}: {e}")
    return False

def log_detection(name, category, frame, location):
    """Log detection event to database and send alert"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Convert frame to JPEG for storage
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        
        # Log detection event
        cursor.execute('''
            INSERT INTO detection_events (person_name, category, last_location, detected_frame)
            VALUES (?, ?, ?, ?)
        ''', (name, category, location, frame_bytes))
        
        conn.commit()
        conn.close()
        
        # Send location-based alert
        send_sms_alert(name, category, location)
        print(f"Detection logged: {name} ({category}) at {location}")
        return True
    except Exception as e:
        print(f"Error logging detection: {e}")
        return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if (request.form['username'] == ADMIN_USERNAME and 
            request.form['password'] == ADMIN_PASSWORD):
            session['logged_in'] = True
            return redirect(url_for('home'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/add_record', methods=['GET', 'POST'])
def add_record():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        city = request.form['city']
        category = request.form['category']
        details = request.form['details']
        images = request.files.getlist('images')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Add person
            cursor.execute('''
                INSERT INTO known_faces (name, age, city, category, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, age, city, category, details))
            person_id = cursor.lastrowid
            
            # Process face images
            for image in images:
                img_data = face_recognition.load_image_file(image)
                encodings = face_recognition.face_encodings(img_data)
                
                if encodings:
                    # Store each encoding
                    for encoding in encodings:
                        cursor.execute('''
                            INSERT INTO face_encodings (person_id, encoding)
                            VALUES (?, ?)
                        ''', (person_id, pickle.dumps(encoding)))
            
            conn.commit()
            return redirect(url_for('home'))
            
        except Exception as e:
            print(f"Error adding record: {e}")
            conn.rollback()
            return "Error adding record", 500
        finally:
            conn.close()
            
    return render_template('add_record.html')

@app.route('/view_records')
def view_records():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT name, age, city, category, details
        FROM known_faces
        ORDER BY name
    ''')
    records = cursor.fetchall()
    conn.close()
    
    return render_template('view_records.html', records=records)

@app.route('/detection_logs')
def detection_logs():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT person_name, category, last_location, time, detected_frame
        FROM detection_events
        ORDER BY time DESC
        LIMIT 100
    ''')
    logs = cursor.fetchall()
    conn.close()
    
    return render_template('detection_logs.html', logs=logs)

@app.route('/live_feed')
def live_feed():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('live_feed.html')

@app.route('/video_feed/<location>')
def video_feed(location):
    return Response(
        generate_frames(location),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

def generate_frames(location):
    while True:
        if location in client_frames:
            frame = client_frames[location]
            _, buffer = cv2.imencode('.jpg', frame)
            frame_data = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')

@app.route('/upload_frame/<location>', methods=['POST'])
def upload_frame(location):
    try:
        # Read and decode frame
        frame_data = request.files['frame'].read()
        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Store frame for display
        client_frames[location] = frame
        
        # Process frame
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        # Get known faces from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT kf.id, kf.name, kf.category, fe.encoding
            FROM known_faces kf
            JOIN face_encodings fe ON kf.id = fe.person_id
        ''')
        known_faces = cursor.fetchall()
        conn.close()
        
        detected_info = []
        for face_encoding in face_encodings:
            for person_id, name, category, known_encoding in known_faces:
                known_encoding = pickle.loads(known_encoding)
                match = face_recognition.compare_faces([known_encoding], face_encoding, tolerance=0.6)[0]
                
                if match:
                    detected_info.append({
                        'name': name,
                        'category': category
                    })
                    log_detection(name, category, frame, location)
                    break
        
        return jsonify({
            'status': 'success',
            'detections': detected_info
        })
        
    except Exception as e:
        print(f"Error processing frame: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
