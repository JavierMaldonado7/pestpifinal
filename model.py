from ultralytics import YOLO
import sys
import io
import re
import matplotlib.pyplot as plt

# Function to parse the captured output for metrics
def parse_output(output):
    epochs, train_losses, val_losses = [], [], []
    # Define your regex patterns to capture the losses and metrics
    epoch_pattern = re.compile(r"Epoch (\d+)/\d+")
    train_loss_pattern = re.compile(r"Train loss: ([\d\.]+)")
    val_loss_pattern = re.compile(r"Val loss: ([\d\.]+)")

    for line in output.getvalue().split('\n'):
        # Find matches in the output
        epoch_match = epoch_pattern.search(line)
        train_loss_match = train_loss_pattern.search(line)
        val_loss_match = val_loss_pattern.search(line)

        # If matches are found, append the values to the respective lists
        if epoch_match:
            epochs.append(int(epoch_match.group(1)))
        if train_loss_match:
            train_losses.append(float(train_loss_match.group(1)))
        if val_loss_match:
            val_losses.append(float(val_loss_match.group(1)))

    return epochs, train_losses, val_losses

# Load the model configuration
model = YOLO("runs\detect\\train10\\weights\\best.pt")

# Redirect stdout to capture training output
old_stdout = sys.stdout
sys.stdout = output = io.StringIO()

# Start training
model.train(data="config.yaml", epochs=20)  # Adjust the number of epochs if needed

# Reset stdout
sys.stdout = old_stdout

# Parse the captured output
epochs, train_losses, val_losses = parse_output(output)

# Plotting the training and validation loss
plt.figure(figsize=(10, 5))
plt.plot(epochs, train_losses, label='Training Loss')
plt.plot(epochs, val_losses, label='Validation Loss')
plt.title('Training and Validation Losses')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show()

# Export the model to ONNX format
path = model.export(format="onnx")
path = model.export
print(f"Model exported to {path}")
