# -*- coding: utf-8 -*-
"""HematoVision_Blood_Cell_Classification.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/18TOF_z9BbfcoPrqRyMWVB1VEdo6Q6jzB
"""

pip install tensorflow opencv-python matplotlib numpy pandas scikit-learn seaborn

import os
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import VGG16, ResNet50, EfficientNetB0
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Ada

!apt

import os
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import VGG16, ResNet50, EfficientNetB0
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam

# Mount Google Drive
from google.colab import drive
drive.mount('/content/drive')

# Download dataset from Kaggle (you'll need your API token)
!pip install kaggle
!mkdir ~/.kaggle
!cp /content/drive/MyDrive/kaggle.json ~/.kaggle/
!chmod 600 ~/.kaggle/kaggle.json
!kaggle datasets download -d paultimothymooney/blood-cells
!unzip blood-cells.zip -d blood-cells

# Define paths
dataset_path = '/content/blood-cells/dataset2-master/dataset2-master/images'
train_path = os.path.join(dataset_path, 'TRAIN')
test_path = os.path.join(dataset_path, 'TEST')

# Check class distribution
classes = os.listdir(train_path)
print("Classes:", classes)

# Visualize sample images
plt.figure(figsize=(15, 10))
for i, class_name in enumerate(classes):
    for j in range(3):
        img_path = os.path.join(train_path, class_name, os.listdir(os.path.join(train_path, class_name))[j])
        img = cv2.imread(img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        plt.subplot(len(classes), 3, i*3 + j + 1)
        plt.imshow(img)
        plt.title(class_name)
        plt.axis('off')
plt.show()

# Data preprocessing
img_size = 224  # Standard size for transfer learning models
batch_size = 32

# Data augmentation for training
train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest',
    validation_split=0.2  # Using 20% for validation
)

# For validation and test - no augmentation
val_test_datagen = ImageDataGenerator(rescale=1./255)

# Create generators
train_generator = train_datagen.flow_from_directory(
    train_path,
    target_size=(img_size, img_size),
    batch_size=batch_size,
    class_mode='categorical',
    subset='training'
)

val_generator = train_datagen.flow_from_directory(
    train_path,
    target_size=(img_size, img_size),
    batch_size=batch_size,
    class_mode='categorical',
    subset='validation'
)

test_generator = val_test_datagen.flow_from_directory(
    test_path,
    target_size=(img_size, img_size),
    batch_size=batch_size,
    class_mode='categorical',
    shuffle=False
)

def create_model(base_model_name='VGG16', num_classes=4):
    # Select base model
    if base_model_name == 'VGG16':
        base_model = VGG16(weights='imagenet', include_top=False, input_shape=(img_size, img_size, 3))
    elif base_model_name == 'ResNet50':
        base_model = ResNet50(weights='imagenet', include_top=False, input_shape=(img_size, img_size, 3))
    elif base_model_name == 'EfficientNet':
        base_model = EfficientNetB0(weights='imagenet', include_top=False, input_shape=(img_size, img_size, 3))
    else:
        raise ValueError("Unknown base model name")

    # Freeze base model layers
    base_model.trainable = False

    # Create new model on top
    inputs = tf.keras.Input(shape=(img_size, img_size, 3))
    x = base_model(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(256, activation='relu')(x)
    x = layers.Dropout(0.5)(x)
    outputs = layers.Dense(num_classes, activation='softmax')(x)

    model = tf.keras.Model(inputs, outputs)

    model.compile(optimizer=Adam(learning_rate=0.001),
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])

    return model

model = create_model(base_model_name='VGG16')
model.summary()

from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau

# Callbacks
checkpoint = ModelCheckpoint('best_model.keras',  # Changed from .h5 to .keras
                            monitor='val_accuracy',
                            save_best_only=True,
                            mode='max',
                            verbose=1)

early_stopping = EarlyStopping(monitor='val_loss',
                              patience=5,
                              restore_best_weights=True)

reduce_lr = ReduceLROnPlateau(monitor='val_loss',
                              factor=0.2,
                              patience=3,
                              min_lr=0.00001,
                              verbose=1)

# Training
history = model.fit(
    train_generator,
    steps_per_epoch=train_generator.samples // batch_size,
    validation_data=val_generator,
    validation_steps=val_generator.samples // batch_size,
    epochs=30,
    callbacks=[checkpoint, early_stopping, reduce_lr],
    verbose=1
)

# Load best model

model = tf.keras.models.load_model('best_model.h5')

# Evaluate on test set



test_loss, test_acc = model.evaluate(test_generator)

print(f'Test Accuracy: {test_acc*100:.2f}%')

# Generate predictions

y_pred = model.predict(test_generator)

y_pred_classes = np.argmax(y_pred, axis=1)

y_true = test_generator.classes

# Classification report

print(classification_report(y_true, y_pred_classes, target_names=classes))

# Confusion matrix

cm = confusion_matrix(y_true, y_pred_classes)

plt.figure(figsize=(8, 6))

sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=classes, yticklabels=classes)

plt.title('Confusion Matrix')

plt.xlabel('Predicted')

plt.ylabel('True')

plt.show()

# Plot training history

plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)

plt.plot(history.history['accuracy'], label='Training Accuracy')

plt.plot(history.history['val_accuracy'], label='Validation Accuracy')

plt.title('Accuracy Over Epochs')

plt.legend()

plt.subplot(1, 2, 2)

plt.plot(history.history['loss'], label='Training Loss')

plt.plot(history.history['val_loss'], label='Validation Loss')

plt.title('Loss Over Epochs')

plt.legend()

plt.show()

# Load best model
model = tf.keras.models.load_model('best_model.keras')

# Evaluate on test set
test_loss, test_acc = model.evaluate(test_generator)
print(f'Test Accuracy: {test_acc*100:.2f}%')

# Generate predictions
y_pred = model.predict(test_generator)
y_pred_classes = np.argmax(y_pred, axis=1)
y_true = test_generator.classes

# Classification report
print(classification_report(y_true, y_pred_classes, target_names=classes))

# Confusion matrix
cm = confusion_matrix(y_true, y_pred_classes)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=classes, yticklabels=classes)
plt.title('Confusion Matrix')
plt.xlabel('Predicted')
plt.ylabel('True')
plt.show()

# Plot training history
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.plot(history.history['accuracy'], label='Training Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.title('Accuracy Over Epochs')
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(history.history['loss'], label='Training Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.title('Loss Over Epochs')
plt.legend()
plt.show()

# Save the final model
model.save('hematolvision_final_model.keras')

# Convert to TensorFlow Lite for mobile deployment (optional)
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

with open('hematolvision_model.tflite', 'wb') as f:
    f.write(tflite_model)

import cv2
import numpy as np
import matplotlib.pyplot as plt

def automated_cell_count(image_path, img_size=224):  # Added img_size as parameter
    # Load image
    img = cv2.imread(image_path)

    # Check if image was loaded correctly
    if img is None:
        raise FileNotFoundError(f"Image not found or invalid path: {image_path}")

    # Preprocess
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (img_size, img_size))
    img = img / 255.0  # Normalize to [0, 1]
    img = np.expand_dims(img, axis=0)  # Add batch dimension

    # Predict
    pred = model.predict(img, verbose=0)  # Silent prediction
    class_idx = np.argmax(pred)
    confidence = np.max(pred)
    class_name = classes[class_idx]  # Ensure `classes` is defined

    # Display
    plt.imshow(img[0])
    plt.title(f'Predicted: {class_name} ({confidence*100:.2f}%)')
    plt.axis('off')
    plt.show()

    return class_name, confidence

# Example usage
image_path = '/content/blood-cells/dataset2-master/dataset2-master/images/TEST/NEUTROPHIL/_0_222.jpeg'
try:
    cell_type, confidence = automated_cell_count(image_path)
    print(f"Cell Type: {cell_type}, Confidence: {confidence*100:.2f}%")
except Exception as e:
    print(f"Error: {e}")

def diagnose_condition(cell_counts):
    """
    cell_counts: dictionary with counts for each cell type
    Example: {'EOSINOPHIL': 50, 'LYMPHOCYTE': 200, 'MONOCYTE': 30, 'NEUTROPHIL': 150}
    """
    total_cells = sum(cell_counts.values())
    percentages = {k: (v/total_cells)*100 for k, v in cell_counts.items()}

    # Basic diagnostic rules (simplified for example)
    conditions = []

    # Check for potential leukemia
    if percentages['LYMPHOCYTE'] > 50 and percentages['NEUTROPHIL'] < 20:
        conditions.append("Potential Lymphocytic Leukemia")

    # Check for potential anemia
    if percentages['EOSINOPHIL'] > 10:
        conditions.append("Possible Parasitic Infection or Allergic Reaction")
    if percentages['MONOCYTE'] > 12:
        conditions.append("Possible Chronic Inflammation or Infection")

    if not conditions:
        conditions.append("Normal blood cell distribution detected")

    return percentages, conditions

# Example usage
sample_counts = {'EOSINOPHIL': 45, 'LYMPHOCYTE': 210, 'MONOCYTE': 35, 'NEUTROPHIL': 140}
percentages, diagnosis = diagnose_condition(sample_counts)

print("Blood Cell Percentages:")
for cell, percent in percentages.items():
    print(f"{cell}: {percent:.1f}%")

print("\nDiagnostic Indicators:")
for condition in diagnosis:
    print(f"- {condition}")

# This would typically be implemented as a Flask/FastAPI service
# Here's a simplified Colab version

from IPython.display import display, HTML
import ipywidgets as widgets

# Create a simple UI
upload = widgets.FileUpload(accept='.jpg,.jpeg,.png', multiple=False)
button = widgets.Button(description="Analyze")
output = widgets.Output()

def on_button_click(b):
    with output:
        output.clear_output()
        if not upload.value:
            print("Please upload an image first")
            return

        # Get the uploaded file
        for filename, data in upload.value.items():
            with open(filename, 'wb') as f:
                f.write(data['content'])

            # Analyze the image
            cell_type, confidence = automated_cell_count(filename)
            print(f"Analysis Result:")
            print(f"Cell Type: {cell_type}")
            print(f"Confidence: {confidence*100:.2f}%")

            # Basic diagnostic suggestion
            if cell_type == 'LYMPHOCYTE' and confidence > 0.7:
                print("\nNote: Elevated lymphocytes may indicate viral infection or lymphocytic leukemia.")
            elif cell_type == 'NEUTROPHIL' and confidence > 0.7:
                print("\nNote: Elevated neutrophils often indicate bacterial infection.")

button.on_click(on_button_click)

display(HTML("<h3>Remote Blood Cell Analysis</h3>"))
display(HTML("<p>Upload a blood cell microscopic image for analysis:</p>"))
display(upload)
display(button)
display(output)

from google.colab import files

# Save your notebook
!jupyter nbconvert --to script HematolVision_Blood_Cell_Classification.ipynb

# Download files
files.download('HematoVision_Blood_Cell_Classification.ipynb')
files.download('HematoVision_Blood_Cell_Classification.py')  # Converted version
files.download('best_model.keras')  # Your trained model
files.download('hematovision_final_model.keras')  # Final model if you have it

!apt-get install git -y
!git config --global user.name "Manvitha0920"
!git config --global user.email "manvithadesu3@gmail.com"

# Commented out IPython magic to ensure Python compatibility.
# Clone your empty GitHub repo

!git clone https://github.com/Manvitha0920/HematolVision.git

# %cd HematolVision

# Save your notebook as a Python script (optional)

!jupyter nbconvert --to script HematoVision_Blood_Cell_Classification.ipynb

# Copy files to the repo folder

!cp /content/HematoVision_Blood_Cell_Classification.ipynb .

!cp /content/HematoVision_Blood_Cell_Classification.py .  # If converted

!cp /content/best_model.keras .  # If you have model files

# Add a README (optional)

!echo "# HematolVision: AI Blood Cell Classifier" > README.md

# Push to GitHub

!git add .

!git commit -m "First commit: Added Colab notebook and model"

!git push origin main