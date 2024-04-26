#!/usr/bin/env python3
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import cv2
from ultralytics import YOLO
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://uinvwsoqhrrdir:61030dacbc95ed5d0e86a87fda8166b1b58bf787e14170dab2dc52df3a1f84d0@ec2-52-5-167-89.compute-1.amazonaws.com:5432/d192656rsmtm0u'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '61030dacbc95ed5d0e86a87fda8166b1b58bf787e14170dab2dc52df3a1f84d0'

db = SQLAlchemy(app)

# Define the Alert model
class Alert(db.Model):
    __tablename__ = 'alerts'
    alert_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    pi_id = db.Column(db.Integer, nullable=False)
    alert_type = db.Column(db.String(20), nullable=False)
    alert_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    alert_isactive = db.Column(db.Boolean, default=True, nullable=False)

# Directory setup
IMAGES_DIR = '/path/to/image_test'  # Adjust path for Linux
OUTPUT_DIR = '/path/to/results'
DETECTED_IMAGES_DIR = os.path.join(OUTPUT_DIR, 'detected')

if not os.path.exists(DETECTED_IMAGES_DIR):
    os.makedirs(DETECTED_IMAGES_DIR)

model_path = '/path/to/best.pt'
model = YOLO(model_path)
threshold = 0.6

class ImageEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            self.process_image(event.src_path)

    def process_image(self, image_path):
        frame = cv2.imread(image_path)
        results = model(frame)[0]

        detected = False
        for result in results.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = result
            if score > threshold:
                detected = True
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 4)
                cv2.putText(frame, results.names[int(class_id)].upper(), (int(x1), int(y1 - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 0), 3, cv2.LINE_AA)

                new_alert = Alert(
                    user_id=1,  # Assuming user_id and pi_id are predefined
                    pi_id=1,
                    alert_type=results.names[int(class_id)],
                    alert_date=datetime.utcnow(),
                    alert_isactive=True
                )
                db.session.add(new_alert)
                db.session.commit()

        if detected:
            output_path = os.path.join(DETECTED_IMAGES_DIR, os.path.basename(image_path))
            cv2.imwrite(output_path, frame)
        else:
            os.remove(image_path)  # Delete images with no detections

if __name__ == '__main__':
    db.create_all()
    event_handler = ImageEventHandler()
    observer = Observer()
    observer.schedule(event_handler, IMAGES_DIR, recursive=False)
    observer.start()
    app.run(debug=True, host='0.0.0.0', port=5000)
    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
