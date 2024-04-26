import os
import cv2
from ultralytics import YOLO

IMAGES_DIR = 'C:\\Users\\jaime\\PycharmProjects\\flaskProject\\image_test'
OUTPUT_DIR = 'C:\\Users\\jaime\\PycharmProjects\\flaskProject\\results'


if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

model_path = 'runs\\detect\\train4\\weights\\best.pt'

# Load a model
model = YOLO(model_path)  # load a custom model

threshold = 0.6

for image_file in os.listdir(IMAGES_DIR):
    if image_file.endswith(('.jpg', '.jpeg', '.png')):  # Add more supported image formats if needed
        image_path = os.path.join(IMAGES_DIR, image_file)

        # Read the image
        frame = cv2.imread(image_path)
        H, W, _ = frame.shape

        results = model(frame)[0]

        for result in results.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = result
            if score > threshold:
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 4)
                cv2.putText(frame, results.names[int(class_id)].upper(), (int(x1), int(y1 - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 0), 3, cv2.LINE_AA)

        output_path = os.path.join(OUTPUT_DIR, f'{os.path.splitext(image_file)[0]}_out.jpg')
        cv2.imwrite(output_path, frame)

print("Object detection on images in the folder completed.")