# **📌 AI-Powered Missing Person and Criminal Identification and Police Alert System**

## **🔹 Overview**
This project is a **real-time facial recognition and alert system** that identifies **missing persons and criminals** based on an existing database and notifies the police or designated authorities via **SMS alerts**. The system captures live video feeds from different locations, processes frames to detect faces, compares them against stored records, and logs the results.

## **🔹 Features**
- ✅ **Face Recognition:** Uses deep learning to match faces from live video feeds.
- ✅ **Live Video Streaming:** Captures and processes frames from multiple locations.
- ✅ **Automated Alerts:** Sends SMS notifications to location-based authorities via **Twilio API**.
- ✅ **Detection Logging:** Stores event details, including face images, timestamps, and locations.
- ✅ **Web Dashboard:** Allows **secure admin login**, record management, and viewing detection logs.
- ✅ **Database Management:** Stores known face encodings, missing person/criminal data, and detection logs.

---

## **🚀 Tech Stack**
- **Backend:** Flask (Python)
- **Frontend:** HTML, CSS (Jinja Templates)
- **Database:** SQLite (stores person details, face encodings, and detection logs)
- **Machine Learning:** face_recognition (for facial detection & matching)
- **Computer Vision:** OpenCV (for processing video frames)
- **Cloud API:** Twilio (for sending SMS alerts)

---




---

## **📌 How It Works?**
1️⃣ **Admin logs in** to the web dashboard.  

![ai1](https://github.com/user-attachments/assets/095d9220-554d-409d-a4bc-53c9397c2a9d)

2️⃣ **New records** (missing persons/criminals) are added with images. 
![ai2](https://github.com/user-attachments/assets/44d164ab-0c13-46e5-b1f9-047668bec2c0)

3️⃣ **Live video feeds** are received from multiple locations.  
![ai3](https://github.com/user-attachments/assets/e8c7761b-26b2-4d79-936b-495ba10cb02e)

4️⃣ **Face recognition** checks for matches against the database.  
5️⃣ If a match is found, the system:
   - Logs the detection event in the database  
   - **Sends an SMS alert** to the location-based contact  
   - Displays the detection on the dashboard  
6️⃣ Admin can **view logs, manage records, and monitor live feeds**.
![ai4](https://github.com/user-attachments/assets/2b94a1f7-5932-4ad8-8dbc-b8f74610493a) ![ai5](https://github.com/user-attachments/assets/aff5a715-1a8d-4b42-aa71-978bf2631b64)



---



---

## **📌 API Endpoints**
| Route               | Method | Description |
|---------------------|--------|-------------|
| `/`                | GET    | Home page (requires login) |
| `/login`           | GET/POST | Admin login |
| `/logout`          | GET    | Logout admin |
| `/add_record`      | GET/POST | Add missing person/criminal record |
| `/view_records`    | GET    | View all records |
| `/detection_logs`  | GET    | View detection logs |
| `/live_feed`       | GET    | View real-time camera feed |
| `/video_feed/<location>` | GET | Stream video for a location |
| `/upload_frame/<location>` | POST | Upload video frames from client devices |

---

## **🔐 Security Measures**
- **Session-based Authentication**: Only authorized users can access the dashboard.  
- **Cooldown System for SMS Alerts**: Prevents spam by restricting alerts to a **5-minute window** per individual per location.  
- **Data Encryption**: Face encodings are stored securely in the database.  

---

## **🛠 Future Improvements**
- 🔹 Integration with **cloud storage** for scalable face database  
- 🔹 Advanced **deep learning models** for improved recognition accuracy  
- 🔹 Integration with **CCTV systems** for large-scale deployment  
- 🔹 Websocket-based **real-time alerts** instead of SMS  

