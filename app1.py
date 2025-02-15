# from flask import Flask, render_template, request, redirect, url_for, Response, jsonify
# import sqlite3
# import face_recognition
# import numpy as np
# import cv2
# import pickle
# import threading
# from datetime import datetime

# app = Flask(__name__, template_folder='templates')

# # Database connection helper
# def get_db_connection():
#     return sqlite3.connect('record.db')

# # Record retrieval function
# def get_detection_records():
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute('''
#         SELECT person_name, category, last_location, time 
#         FROM detection_events 
#         ORDER BY time DESC
#     ''')
#     records = cursor.fetchall()
#     conn.close()
#     return records

# def log_detection(name, category, frame, location="Unknown"):
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         _, buffer = cv2.imencode('.jpg', frame)
#         frame_bytes = buffer.tobytes()
        
#         cursor.execute('''
#             INSERT INTO detection_events (person_name, category, last_location, detected_frame)
#             VALUES (?, ?, ?, ?)
#         ''', (name, category, location, frame_bytes))
#         conn.commit()
#         conn.close()
#         print(f"ALERT: {category} detected - {name} at {location}")
#     except Exception as e:
#         print(f"Error logging detection: {e}")

# def get_face_encodings():
#     conn = get_db_connection()
#     cursor = conn.cursor()
    
#     cursor.execute("SELECT person_id, encoding FROM face_encodings")
#     rows = cursor.fetchall()
#     known_encodings = [pickle.loads(row[1]) for row in rows]
#     known_ids = [row[0] for row in rows]
    
#     cursor.execute("SELECT id, name, category FROM known_faces")
#     face_rows = cursor.fetchall()
#     face_dict = {row[0]: {'name': row[1], 'category': row[2]} for row in face_rows}
#     conn.close()
#     return known_encodings, known_ids, face_dict

# client_frames = {}

# @app.route('/')
# def home():
#     return render_template('home.html')

# @app.route('/add_record')
# def add_record():
#     return render_template('add_record.html')

# @app.route('/live_feed')
# def live_feed():
#     return render_template('live_feed.html')

# @app.route('/view_records')
# def view_records():
#     records = get_detection_records()
#     return render_template('view_records.html', records=records)

# @app.route('/add_person', methods=['POST'])
# def add_person():
#     name = request.form['name']
#     age = request.form['age']
#     city = request.form['city']
#     category = request.form['category']
#     details = request.form['details']
#     image_files = request.files.getlist('images')
    
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     try:
#         cursor.execute('''
#         INSERT INTO known_faces (name, age, city, category, details) 
#         VALUES (?, ?, ?, ?, ?)
#         ''', (name, age, city, category, details))
#         person_id = cursor.lastrowid
        
#         encoding_added = False
#         for image_file in image_files:
#             try:
#                 image = face_recognition.load_image_file(image_file)
#                 encodings = face_recognition.face_encodings(image)
#                 for encoding in encodings:
#                     cursor.execute('''
#                     INSERT INTO face_encodings (person_id, encoding) 
#                     VALUES (?, ?)
#                     ''', (person_id, pickle.dumps(encoding)))
#                     encoding_added = True
#             except Exception as e:
#                 print(f"Error processing image {image_file.filename}: {e}")
        
#         if not encoding_added:
#             print("No valid face encodings found for the provided images.")
#     except Exception as e:
#         print(f"Error adding person details to the database: {e}")
#     finally:
#         conn.commit()
#         conn.close()
#     return redirect(url_for('home'))

# @app.route('/video_feed/<client_id>')
# def video_feed(client_id):
#     return Response(generate_frame(client_id),
#                    mimetype='multipart/x-mixed-replace; boundary=frame')

# def generate_frame(client_id):
#     while True:
#         if client_id in client_frames:
#             frame = client_frames[client_id]
#             ret, jpeg = cv2.imencode('.jpg', frame)
#             if ret:
#                 yield (b'--frame\r\n'
#                        b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

# @app.route('/upload_frame/<client_id>', methods=['POST'])
# def upload_frame(client_id):
#     try:
#         data = request.files['frame'].read()
#         nparr = np.frombuffer(data, np.uint8)
#         frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
#         client_frames[client_id] = frame
#         detected_info = process_frame(frame, client_id)
#         return jsonify({"status": "frame processed", "detected_info": detected_info})
#     except Exception as e:
#         print(f"Error processing frame: {e}")
#         return jsonify({"status": "error", "message": str(e)}), 500

# def process_frame(frame, location="Unknown"):
#     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     face_locations = face_recognition.face_locations(rgb_frame)
#     face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    
#     known_encodings, known_ids, face_dict = get_face_encodings()
#     detected_info = []
    
#     for face_encoding in face_encodings:
#         matches = face_recognition.compare_faces(known_encodings, face_encoding)
#         if True in matches:
#             first_match_index = matches.index(True)
#             person_id = known_ids[first_match_index]
#             person_info = face_dict[person_id]
#             name = person_info['name']
#             category = person_info['category']
#             detected_info.append({'name': name, 'category': category})
#             log_detection(name, category, frame, location)
    
#     return detected_info

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True)



from flask import Flask, render_template, request, redirect, url_for, Response, jsonify, session
import sqlite3
import face_recognition
import numpy as np
import cv2
import pickle
import threading
from datetime import datetime

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'  # Required for using sessions

# Hardcoded login credentials
VALID_USERNAME = 'admin'
VALID_PASSWORD = 'password'

# Database connection helper
def get_db_connection():
    return sqlite3.connect('record.db')

# Record retrieval function
def get_detection_records():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT person_name, category, last_location, time 
        FROM detection_events 
        ORDER BY time DESC
    ''')
    records = cursor.fetchall()
    conn.close()
    return records

def log_detection(name, category, frame, location="Unknown"):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        
        cursor.execute('''
            INSERT INTO detection_events (person_name, category, last_location, detected_frame)
            VALUES (?, ?, ?, ?)
        ''', (name, category, location, frame_bytes))
        conn.commit()
        conn.close()
        print(f"ALERT: {category} detected - {name} at {location}")
    except Exception as e:
        print(f"Error logging detection: {e}")

def get_face_encodings():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT person_id, encoding FROM face_encodings")
    rows = cursor.fetchall()
    known_encodings = [pickle.loads(row[1]) for row in rows]
    known_ids = [row[0] for row in rows]
    
    cursor.execute("SELECT id, name, category FROM known_faces")
    face_rows = cursor.fetchall()
    face_dict = {row[0]: {'name': row[1], 'category': row[2]} for row in face_rows}
    conn.close()
    return known_encodings, known_ids, face_dict

client_frames = {}

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Validate credentials
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

#Home Route
@app.route('/')
def home():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/add_record')
def add_record():
    return render_template('add_record.html')

@app.route('/live_feed')
def live_feed():
    return render_template('live_feed.html')

@app.route('/detection_logs')
def detection_logs():
    # Fetch detection logs from the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT person_name, category, last_location, time, detected_frame 
        FROM detection_events 
        ORDER BY time DESC
    ''')
    logs = cursor.fetchall()
    conn.close()
    
    # Render the logs page
    return render_template('detection_logs.html', logs=logs)


@app.route('/view_records')
def view_records():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch known faces and their corresponding encodings from the database
    cursor.execute('''
        SELECT kf.id, kf.name, kf.age, kf.city, kf.category, kf.details, fe.encoding
        FROM known_faces kf
        LEFT JOIN face_encodings fe ON kf.id = fe.person_id
    ''')
    
    known_faces_data = cursor.fetchall()
    conn.close()

    # Prepare the data to pass to the template
    known_faces = []
    for data in known_faces_data:
        person_id, name, age, city, category, details, encoding_binary = data
        if encoding_binary:
            encoding = pickle.loads(encoding_binary).tolist()  # Convert to list
        else:
            encoding = None
        known_faces.append({
            'name': name,
            'age': age,
            'city': city,
            'category': category,
            'details': details,
            'encoding': encoding
        })
    
    # Render the page with known faces and their encodings
    return render_template('view_records.html', known_faces=known_faces)




@app.route('/video_feed/<client_id>')
def video_feed(client_id):
    return Response(generate_frame(client_id),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_frame(client_id):
    while True:
        if client_id in client_frames:
            frame = client_frames[client_id]
            ret, jpeg = cv2.imencode('.jpg', frame)
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

@app.route('/upload_frame/<client_id>', methods=['POST'])
def upload_frame(client_id):
    try:
        data = request.files['frame'].read()
        nparr = np.frombuffer(data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        client_frames[client_id] = frame
        detected_info = process_frame(frame, client_id)
        return jsonify({"status": "frame processed", "detected_info": detected_info})
    except Exception as e:
        print(f"Error processing frame: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def process_frame(frame, location="Unknown"):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    
    known_encodings, known_ids, face_dict = get_face_encodings()
    detected_info = []
    
    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_encodings, face_encoding)
        if True in matches:
            first_match_index = matches.index(True)
            person_id = known_ids[first_match_index]
            person_info = face_dict[person_id]
            name = person_info['name']
            category = person_info['category']
            detected_info.append({'name': name, 'category': category})
            log_detection(name, category, frame, location)
    
    return detected_info

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
