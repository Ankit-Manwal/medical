import tensorflow as tf
import numpy as np
from tensorflow.keras.models import load_model
import os


class_names=[   
                'Akne',
                'Basal Cell Carcinoma (BCC)',
                'Melanocytic Nevi (NV)',
                'Melanoma',
                'Pigment',
                'Seborrheic Keratoses and other Benign Tumors'
            ]


parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

model_path = os.path.join(parent_dir, 'skin_diseases/skin_diseases_model.h5')

# Load the model
model = tf.keras.models.load_model(model_path, compile=False)  # Set compile=False

def give_skin_diseases_prediction(img_path):
    # Load and preprocess the image
    img = tf.keras.preprocessing.image.load_img(img_path)  # Adjust target_size as per your model's input size
    img_array = tf.keras.preprocessing.image.img_to_array(img)
    img_array = tf.expand_dims(img_array, axis=0)  # Add batch dimension

    # Make predictions
    predictions = model.predict(img_array)
    
    # Get the predicted class and confidence
    predicted_class = class_names[np.argmax(predictions[0])]
    confidence = round(100 * np.max(predictions[0]), 2)

    return {'predicted_class':predicted_class, 'confidence' :confidence}

# # Example usage 
# image_path = os.path.join(parent_dir, 'skin_diseases', 'test dataset', 'Akne', 'image_Akne_28.png')
# result = give_skin_diseases_prediction(model, image_path)
# print(f"Predicted class: {result['predicted_class']}, Confidence: {result['confidence']}%")
