from ultralytics import YOLO
import sys
import io
import re
import matplotlib.pyplot as plt

# Load the model configuration
model = YOLO("runs/detect/train15/weights/best.pt")

# Validate the model
metrics = model.val()  # no arguments needed, dataset and settings remembered
from ultralytics.utils.benchmarks import benchmark

