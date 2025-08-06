import os
# Set the environment variable to avoid OpenMP runtime errors
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import pandas as pd
import numpy as np
from tensorflow.keras.models import load_model
import json

import spacy
from spacy.matcher import PhraseMatcher


# Load the spaCy model
nlp = spacy.load('en_core_web_sm')

#path of parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


# Load the dictionary from the json file
json_path = os.path.join(parent_dir, 'general_conditions/model_detail.json')
data = json.load(open(json_path, "r") )

# Load the model
model_path = os.path.join(parent_dir, 'general_conditions/'+data["model_path"])
loaded_model = load_model(model_path)

# Load the categories
diseases_classes = data["diseases_classes"]
symptoms_classes = data["all_symptoms"]
symptoms_classes = [s.replace("_", " ") for s in symptoms_classes if isinstance(s, str)]


# Load the symptom_Description and symptom_precaution_path files
symptom_Description_path = os.path.join(parent_dir, "general_conditions/dataset/symptom_Description.csv")
df_des = pd.read_csv(symptom_Description_path)

symptom_precaution_path = os.path.join(parent_dir, "general_conditions/dataset/symptom_precaution.csv")
df_recom = pd.read_csv(symptom_precaution_path)




# Function to find symptoms in a sentence
def find_symptoms(sentence, symptoms=symptoms_classes):
    # Step 1: Create a PhraseMatcher object
    matcher = PhraseMatcher(nlp.vocab)
    
    # Step 2: Convert symptoms into spaCy doc objects
    patterns = [nlp(text) for text in symptoms]
    matcher.add("SYMPTOMS", patterns)
    
    # Step 3: Process the sentence with spaCy
    doc = nlp(sentence)
    
    # Step 4: Find matches in the processed sentence
    matches = matcher(doc)
    
    # Step 5: Extract matched symptoms
    matched_symptoms = [doc[start:end].text for match_id, start, end in matches]
    
    return matched_symptoms



# Function to create a binary array for matched symptoms
def symptoms_to_binary(matched_symptoms, all_symptoms):
    lis= [1 if symptom in matched_symptoms else 0 for symptom in all_symptoms]
    return np.array(lis)


def get_prediction_with_confidence(model, x_input, diseases_classes=diseases_classes):
    # Predict probabilities
    predictions = model.predict(x_input.reshape(1,-1))
    
    # Get the predicted class (index of the highest probability)
    predicted_class = np.array(diseases_classes) [np.argmax(predictions, axis=1)]
    
    # Get the confidence score (highest probability)
    confidence_score = np.max(predictions, axis=1)
    
    return predicted_class[0], confidence_score[0]



def give_description(predicted_disease):
    description = df_des[df_des['Disease'] == predicted_disease]["Description"].item()
    return description


def give_recommendation(predicted_disease):
    recommendations = df_recom[df_recom['Disease'] == predicted_disease]
    recommendations = [recommendations[col].item() for col in recommendations.drop(columns='Disease').columns if  not pd.isna(recommendations[col].item())]
    return recommendations




def give_predicted_result(sentence):
    
    matched_symptoms=find_symptoms(sentence, symptoms=symptoms_classes)
    if not matched_symptoms:
        return None

    inp=symptoms_to_binary(matched_symptoms,symptoms_classes)
    predicted_disease, confidence_score = get_prediction_with_confidence(loaded_model, inp)
    description= give_description(predicted_disease)
    recommendations= give_recommendation(predicted_disease)

    return {"predicted_disease":predicted_disease,
             "confidence_score":confidence_score,
             "description":description,
             "recommendations":recommendations}


# r=give_predicted_result("I have been experiencing chills , fatigue, my eyes are red and pain in chest and muscle with high fever and cough and running nose. i am feeling irritation in throat and headache")
# print(r["predicted_disease"])