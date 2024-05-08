from ultralytics import YOLO
import sys
import io
import re
import matplotlib.pyplot as plt

# Load the model configuration
model = YOLO("runs/detect/train15/weights/best.pt")

# Validate the model
metrics = model.val()  # no arguments needed, dataset and settings remembered

# Print the metrics to understand the results
print("Validation Metrics:")
for metric, value in metrics.items():
    print(f"{metric}: {value}")

# Example plots (adjust according to the actual metric keys in your 'metrics' dictionary)
if 'precision' in metrics and 'recall' in metrics:
    # Creating a bar plot for precision and recall
    plt.figure(figsize=(10, 5))
    plt.bar(['Precision', 'Recall'], [metrics['precision'], metrics['recall']])
    plt.title('Precision and Recall of the Model')
    plt.ylabel('Value')
    plt.show()

# Add more plots as needed based on other metrics
