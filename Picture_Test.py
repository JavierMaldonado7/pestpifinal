#!/usr/bin/env python3
import os
import cv2
import psycopg2
from psycopg2 import sql
from datetime import datetime
from shutil import move
from ultralytics import YOLO
import threading
import time

IMAGES_DIR = '/home/cs/MotionFiles'
DETECTED_IMAGES_DIR = '/home/cs/Desktop/output/detected'

if not os.path.exists(DETECTED_IMAGES_DIR):
    os.makedirs(DETECTED_IMAGES_DIR)

model_path = 'best(1).pt'
model = YOLO(model_path)  # Load a custom model
threshold = 0.8

# Database connection parameters
dbname = "d12fhtfr8lc1ks"
user = "vevnxnnnehlhcr"
password = "bc565cc08ffecbeeac4ebda9e3362a43eb6b28031322c93304b87bb71a4314d0"
host = "ec2-52-73-67-148.compute-1.amazonaws.com"
port = "5432"

def send_alert_to_db(user_id, pi_id, alert_type, image_path):
    conn = None
    try:
        conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        cursor = conn.cursor()
        frame = cv2.imread(image_path)
        if frame is None:
            raise Exception(f"Unable to load image from {image_path}")
        image_data = cv2.imencode('.jpg', frame)[1].tobytes()  # Convert image to bytes
        query = sql.SQL("""
            INSERT INTO alerts (user_id, pi_id, alert_type, alert_date, alert_isactive, image)
            VALUES (%s, %s, %s, %s, %s, %s)
        """)
        values = (user_id, pi_id, alert_type, datetime.now(), True, image_data)
        cursor.execute(query, values)
        conn.commit()
        print("Alert and first image stored successfully.")
    except Exception as e:
        print(f"Failed to send alert to DB: {e}")
    finally:
        if conn:
            conn.close()

def delete_image(image_path):
    if os.path.exists(image_path):
        os.remove(image_path)
        print(f"Deleted {image_path}")

def process_images(image_paths):
    detected = False
    for image_path in image_paths:
        frame = cv2.imread(image_path)
        if frame is None:
            print(f"Failed to read image: {image_path}")
            delete_image(image_path)
            continue

        results = model(frame)[0]
        if results.boxes.data.size(0) > 0:  # Check if there are any detections
            for result in results.boxes.data.tolist():
                x1, y1, x2, y2, score, class_id = result
                print(f"Detections: {results.names[int(class_id)]} with score {score}")  # Debug print
                if score > threshold:
                    detected = True
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 4)
                    cv2.putText(frame, results.names[int(class_id)].upper(), (int(x1), int(y1 - 10)),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 255), 3, cv2.LINE_AA)
                    output_path = os.path.join(DETECTED_IMAGES_DIR, os.path.basename(image_path))
                    cv2.imwrite(output_path, frame)
                    send_alert_to_db(2, 2, results.names[int(class_id)], output_path)
                    move(image_path, output_path)
                    break  # Exit after processing the first detected image
            if detected:
                # If detection occurs, break and delete all remaining images
                for path in image_paths:
                    delete_image(path)
                return
        else:
            print(f"No valid detections found for {image_path}")  # Debug print
        delete_image(image_path)  # If no detections, delete the image

import time

def continuous_check():
    while True:
      # Wait for 10 seconds before checking the directory again
        current_files = [os.path.join(IMAGES_DIR, file_name) for file_name in os.listdir(IMAGES_DIR)]
        if current_files:
            for file_path in sorted(current_files):
                time.sleep(5)  # Wait for 5 seconds before processing each file
                process_images([file_path])  # Process one file at a tim

if __name__ == '__main__':
    continuous_check()