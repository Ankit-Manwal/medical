import os
# Set the environment variable to avoid OpenMP runtime errors
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import pandas as pd
import numpy as np
from tensorflow.keras.models import load_model
import json

import spacy
from spacy.matcher import PhraseMatcher


# Load the spaCy model with graceful fallback
try:
    nlp = spacy.load('en_core_web_sm')
except Exception:
    try:
        # Fallback to a blank English pipeline if the model isn't installed
        nlp = spacy.blank('en')
    except Exception:
        # Final fallback: create minimal tokenizer-only pipeline
        nlp = spacy.blank('en')

#path of parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


# Load the dictionary from the json file (new folder name)
json_path = os.path.join(parent_dir, 'general_symptom_based_detection/model_detail.json')
data = json.load(open(json_path, "r") )

# Load the model
model_path = os.path.join(parent_dir, 'general_symptom_based_detection/'+data["model_path"])
loaded_model = load_model(model_path)

# Load the categories
diseases_classes = data["diseases_classes"]
symptoms_classes = data["all_symptoms"]
symptoms_classes = [s.replace("_", " ") for s in symptoms_classes if isinstance(s, str)]


# Load the symptom_Description and symptom_precaution_path files
symptom_Description_path = os.path.join(parent_dir, "general_symptom_based_detection/dataset/symptom_Description.csv")
df_des = pd.read_csv(symptom_Description_path)

symptom_precaution_path = os.path.join(parent_dir, "general_symptom_based_detection/dataset/symptom_precaution.csv")
df_recom = pd.read_csv(symptom_precaution_path)


# Load model_detail.json for disease-specific symptoms
model_detail_path = os.path.join(parent_dir, 'general_symptom_based_detection/model_detail.json')
with open(model_detail_path, 'r') as f:
    model_detail = json.load(f)

# Load dataset for follow-up questions
dataset_path = os.path.join(parent_dir, 'general_symptom_based_detection/dataset/dataset.csv')
df_dataset = pd.read_csv(dataset_path)


# Load available_tests from all_disease_specific_model_details.json
all_disease_specific_model_details_file = os.path.join(parent_dir, 'resources/all_disease_specific_model_details.json')
with open(all_disease_specific_model_details_file, 'r') as f:
    all_disease_specific_model_details = json.load(f)



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
    if not predicted_disease:
     return ""
    description = df_des[df_des['Disease'] == predicted_disease]["Description"].item()
    return description
# "A condition with high sugar levels."

def give_recommendation(predicted_disease):
    if not predicted_disease:
        return []
    recommendations = df_recom[df_recom['Disease'] == predicted_disease]
    recommendations = [recommendations[col].item() for col in recommendations.drop(columns='Disease').columns if  not pd.isna(recommendations[col].item())]
    return recommendations
# ["Exercise daily", "Monitor blood sugar"]

def get_disease_details(disease_list):
    if not disease_list:
        return []
    return [
        {
            "disease": d,
            "description": give_description(d),
            "recommendations": give_recommendation(d)
        }
        for d in disease_list
    ]
# [
#   {
#     "disease": "Diabetes",
#     "description": "A condition with high sugar levels.",
#     "recommendations": ["Exercise daily", "Monitor blood sugar"]
#   },
#   {
#     "disease": "UnknownDisease",
#     "description": "",
#     "recommendations": []
#   }
# ]



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

# [
#   {
#     "disease": "Diabetes",
#     "description": "A condition with high sugar levels.",
#     "recommendations": ["Exercise daily", "Monitor blood sugar"]
#   },
#   {
#     "disease": "UnknownDisease",
#     "description": "",
#     "recommendations": []
#   }
# ]


def get_disease_symptoms(disease_name):
    """Get all symptoms associated with a specific disease from model_detail.json"""
    # Get symptoms directly from model_detail.json
    condition_specific_symptoms = model_detail.get('condition_specific_symptoms', {})
    symptoms = condition_specific_symptoms.get(disease_name, [])
    
    # # Debug: print what we're getting
    # print(f"DEBUG: get_disease_symptoms for {disease_name}")
    # print(f"DEBUG: condition_specific_symptoms type: {type(condition_specific_symptoms)}")
    # print(f"DEBUG: symptoms type: {type(symptoms)}")
    # print(f"DEBUG: symptoms value: {symptoms}")
    
    if symptoms:
        return symptoms
    
    # Fallback to the original method if not found in JSON
    disease_data = df_dataset[df_dataset['Disease'] == disease_name]
    all_symptoms = set()
    
    for _, row in disease_data.iterrows():
        symptoms = [s for s in row[1:] if pd.notna(s) and s.strip()]
        all_symptoms.update(symptoms)
    
    return list(all_symptoms)



def give_top_predictions(symptoms, top_k=None):
    """
    Predict top_k diseases (or all if top_k=None) from given symptoms.
    'symptoms' can be a string, list, or set of symptom strings.
    Returns a list of dicts: { 'disease': ..., 'confidence': ... }
    """
    print(f"\n\n[DEBUG] give_top_predictions***** backend function******* called with symptoms: {symptoms}, top_k: {top_k}\n\n")
    # Case 1: Input is a string → use NLP matcher to extract known symptoms

    # function to remove underscores from symptoms
    symptoms= symptoms.replace("_", " ")
    matched_symptoms = []
    if isinstance(symptoms, str):
        matched_symptoms = find_symptoms(symptoms, symptoms=symptoms_classes)

    # Case 2: Input is a list or set → directly match against known symptoms
    elif isinstance(symptoms, (list, set)):
        matched_symptoms = [s for s in symptoms if s in symptoms_classes]

    else:
        raise ValueError("symptoms must be a string, list, or set of strings")

    # No matches → return empty list
    if not matched_symptoms:
        # print("symptoms_classes:", symptoms_classes)
        print(f"\n\n[DEBUG] give_top_predictions found no matched symptoms. Returning empty list.\n\n")
        return []

    # Convert to binary vector
    inp = symptoms_to_binary(matched_symptoms, symptoms_classes)

    # Get predictions
    predictions = loaded_model.predict(inp.reshape(1, -1))[0]

    # Create disease-confidence mapping
    all_predictions = [
        {"disease": diseases_classes[i], "confidence": float(predictions[i])}
        for i in range(len(diseases_classes))
    ]

    # Sort by confidence descending
    all_predictions.sort(key=lambda x: x["confidence"], reverse=True)

    # Limit results if top_k is provided
    if top_k is not None:
        all_predictions = all_predictions[:top_k]
    print(f"\n\n[DEBUG] give_top_predictions returning: {all_predictions}\n\n")
    return all_predictions
# [
#     {"disease": "Flu", "confidence": 0.82},
#     {"disease": "Common Cold", "confidence": 0.10},
#     {"disease": "COVID-19", "confidence": 0.05}
# ]


def get_frequency_uniqueness_rarity_percent(condition_specific_symptoms):
    """
    Calculate frequency percentage, rarity percentage, and uniqueness for each symptom.

    Returns a dict like:
    {
        symptom: {
            "frequency_percent": float,  # (count / total diseases) * 100
            "rarity_percent": float,     # 100 - frequency_percent
            "uniqueness": float          # 100 if unique to one disease else 50
        }
    }
    """
    if not condition_specific_symptoms:
        return {}

    total_diseases = len(condition_specific_symptoms)
    frequency_counts = {}

    for disease, symptoms in condition_specific_symptoms.items():
        for symptom in set(symptoms):  # avoid double counting symptoms in same disease
            frequency_counts[symptom] = frequency_counts.get(symptom, 0) + 1

    stats = {}
    for symptom, count in frequency_counts.items():
        frequency_percent = (count / total_diseases) * 100
        rarity_percent = 100 - frequency_percent
        uniqueness = 100 if count == 1 else 50
        stats[symptom] = {
            "frequency_percent": frequency_percent,
            "rarity_percent": rarity_percent,
            "uniqueness": uniqueness
        }

    return stats



def generate_follow_up_questions_from_all(
    all_predictions,
    current_symptoms,
    frequency_uniqueness_rarity_percent,
    symptoms_removed=None,
    max_per_disease=3,
    max_total=10
):
    if symptoms_removed is None:
        symptoms_removed = set()

    # generic_symptoms = {"fever", "cough", "fatigue", "headache"}  # optional filter
    generic_symptoms = set()  # optional filter

    questions = []
    used_symptoms = set()

    # Preload symptoms for all diseases
    disease_symptom_mapping = {}
    for pred in all_predictions:
        disease = pred['disease']
        symptoms = get_disease_symptoms(disease)
        
        disease_symptom_mapping[disease] = set(symptoms) if symptoms else set()
    
    for pred in all_predictions:
        disease = pred['disease']
        conf = pred['confidence']
        disease_symptoms = disease_symptom_mapping[disease]

        # Filter out already known, denied, or generic symptoms
        candidate_symptoms = (
            disease_symptoms
            - current_symptoms
            - symptoms_removed
            - generic_symptoms
        )

        if not candidate_symptoms:
            continue

        # Get symptoms from other diseases
        other_symptoms = set().union(*(v for k, v in disease_symptom_mapping.items() if k != disease))
        symptom_scores = {}

        for s in candidate_symptoms:
            # Get frequency and uniqueness from the provided dictionary, fallback to default values
            freq = frequency_uniqueness_rarity_percent.get(s, {}).get('frequency_percent', 50) / 100
            uniqueness = frequency_uniqueness_rarity_percent.get(s, {}).get('uniqueness', 1.0) /100
            rarity = 1 / freq if freq > 0 else 1.0
            
            # Normalize confidence to decimal (0.0-1.0) for calculations
            # If confidence is already a percentage (>= 1.0), convert to decimal
            normalized_conf = conf / 100.0 if conf >= 1.0 else conf
            
            # Score combines confidence, uniqueness, and rarity (weighted)
            symptom_scores[s] = (normalized_conf * uniqueness) + (0.3 * rarity)

        # Sort symptoms by descending score
        ranked_symptoms = sorted(symptom_scores, key=symptom_scores.get, reverse=True)

        # Pick top symptoms avoiding repeats
        selected_symptoms = [s for s in ranked_symptoms if s not in used_symptoms][:max_per_disease]

        if selected_symptoms:
            used_symptoms.update(selected_symptoms)
            questions.append({
                'disease': disease,
                'symptoms': selected_symptoms,
                'question': f"For {disease} (confidence: {conf:.5f}%), do you have: {', '.join(selected_symptoms)}?",
                'confidence': conf
            })

        if len(used_symptoms) >= max_total:
            break

    return questions
# [
#     {
#         "disease": "Flu",
#         "symptoms": ["muscle pain", "chills"],
#         "question": "For Flu (confidence: 0.82%), do you have: muscle pain, chills?",
#         "confidence": 0.82
#     },
#     ...
# ]




# r=give_predicted_result("I have been experiencing chills , fatigue, my eyes are red and pain in chest and muscle with high fever and cough and running nose. i am feeling irritation in throat and headache")
# print(r["predicted_disease"])