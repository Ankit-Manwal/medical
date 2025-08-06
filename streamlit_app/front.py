import streamlit as st
from streamlit_option_menu import option_menu
import sys
import os
from PIL import Image
import pandas as pd
import numpy as np

# Load CSS styles
def load_css():
    css_file = os.path.join(os.path.dirname(__file__), 'styles.css')
    with open(css_file, 'r') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


# Get the parent directory of the current script
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

# Now you can import the target file using an absolute import
from general_conditions import general_conditions_backendfunction as gen
from diabetes import diabetes_backendfunction as diab
from skin_diseases import skin_diseases_backendfunction as skin
import json

# Load model_detail.json for disease-specific symptoms
model_detail_path = os.path.join(parent_dir, 'general_conditions/model_detail.json')
with open(model_detail_path, 'r') as f:
    model_detail = json.load(f)

# Load dataset for follow-up questions
dataset_path = os.path.join(parent_dir, 'general_conditions/dataset/dataset.csv')
df_dataset = pd.read_csv(dataset_path)



def get_top_predictions(symptoms_text, top_k=3):
    """Get top k predictions with their probabilities"""
    matched_symptoms = gen.find_symptoms(symptoms_text, gen.symptoms_classes)
    if not matched_symptoms:
        return []
    
    inp = gen.symptoms_to_binary(matched_symptoms, gen.symptoms_classes)
    predictions = gen.loaded_model.predict(inp.reshape(1, -1))
    
    # Get top k predictions
    top_indices = np.argsort(predictions[0])[-top_k:][::-1]
    top_predictions = []
    
    for idx in top_indices:
        disease = gen.diseases_classes[idx]
        confidence = predictions[0][idx]
        top_predictions.append({
            'disease': disease,
            'confidence': confidence
        })
    
    return top_predictions


def get_disease_symptoms(disease_name):
    """Get all symptoms associated with a specific disease from model_detail.json"""
    # Get symptoms directly from model_detail.json
    condition_specific_symptoms = model_detail.get('condition_specific_symptoms', {})
    symptoms = condition_specific_symptoms.get(disease_name, [])
    
    if symptoms:
        return symptoms
    
    # Fallback to the original method if not found in JSON
    disease_data = df_dataset[df_dataset['Disease'] == disease_name]
    all_symptoms = set()
    
    for _, row in disease_data.iterrows():
        symptoms = [s for s in row[1:] if pd.notna(s) and s.strip()]
        all_symptoms.update(symptoms)
    
    return list(all_symptoms)


def generate_follow_up_questions(top_predictions, current_symptoms):
    """Generate follow-up questions based on top predictions with unique symptoms"""
    questions = []
    
    # Get all symptoms from all top predictions
    all_prediction_symptoms = set()
    disease_symptom_mapping = {}
    
    for pred in top_predictions:
        disease = pred['disease']
        disease_symptoms = get_disease_symptoms(disease)
        disease_symptom_mapping[disease] = disease_symptoms
        all_prediction_symptoms.update(disease_symptoms)
    
    # Find symptoms that are unique to each disease (not shared with other top predictions)
    for pred in top_predictions:
        disease = pred['disease']
        disease_symptoms = set(disease_symptom_mapping[disease])
        
        # Find symptoms unique to this disease among top predictions
        unique_symptoms = disease_symptoms.copy()
        for other_pred in top_predictions:
            if other_pred['disease'] != disease:
                other_disease_symptoms = set(disease_symptom_mapping[other_pred['disease']])
                unique_symptoms -= other_disease_symptoms
        
        # Find symptoms that are not in current symptoms and are unique
        missing_unique_symptoms = [s for s in unique_symptoms if s not in current_symptoms]
        
        if missing_unique_symptoms:
            # Take up to 3 most unique missing symptoms
            important_symptoms = missing_unique_symptoms[:3]
            question = f"For {disease} (confidence: {pred['confidence']:.2%}), do you have these unique symptoms: {', '.join(important_symptoms)}?"
            questions.append({
                'disease': disease,
                'symptoms': important_symptoms,
                'question': question,
                'confidence': pred['confidence'],
                'unique': True
            })
        else:
            # If no unique symptoms, fall back to any missing symptoms
            missing_symptoms = [s for s in disease_symptoms if s not in current_symptoms]
            if missing_symptoms:
                important_symptoms = missing_symptoms[:3]
                question = f"For {disease} (confidence: {pred['confidence']:.2%}), do you have: {', '.join(important_symptoms)}?"
                questions.append({
                    'disease': disease,
                    'symptoms': important_symptoms,
                    'question': question,
                    'confidence': pred['confidence'],
                    'unique': False
                })
    
    return questions

def update_prediction_with_follow_up(original_symptoms, follow_up_symptoms):
    """Update prediction with additional symptoms from follow-up"""
    all_symptoms = original_symptoms + follow_up_symptoms
    return gen.give_predicted_result(" ".join(all_symptoms))

#streamlit app*******************************************************************************************************************************************
def main():
    # Set page configuration
    st.set_page_config(page_title="Health Assistant",
                    layout="wide",
                    page_icon="🧑‍⚕️")
    
    # Load CSS styles
    load_css()

    # Initialize session state for chat
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_symptoms' not in st.session_state:
        st.session_state.current_symptoms = []
    if 'follow_up_questions' not in st.session_state:
        st.session_state.follow_up_questions = []
    if 'waiting_for_follow_up' not in st.session_state:
        st.session_state.waiting_for_follow_up = False

    # sidebar for navigation
    with st.sidebar:
        selected = option_menu('Multiple Disease Prediction System',

                            ['Medical Condition Predictor',
                                'Diabetes Prediction',
                                'Skin Disease Prediction'],
                            menu_icon='hospital-fill',
                            icons=['activity', 'heart','bandaid-fill'],
                            default_index=0)

    # medical Prediction Page
    if selected == 'Medical Condition Predictor':
        st.title("General Medical Condition Predictor")
        st.write("Describe your symptoms and I'll help you identify possible conditions through a conversation.")

        # Display chat history with styled messages
        if st.session_state.chat_history:
            st.write("### Conversation History")
            
            for i, message in enumerate(st.session_state.chat_history):
                if message['type'] == 'user':
                    # User message with CSS class
                    st.markdown(f"""
                    <div class="user-message-alt">
                        <strong>You:</strong> {message['content']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                elif message['type'] == 'assistant':
                    # Assistant message with CSS class
                    st.markdown(f"""
                    <div class="assistant-message-alt">
                        <strong>Assistant:</strong> {message['content']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                elif message['type'] == 'prediction':
                    # Prediction message with CSS class
                    st.markdown(f"""
                    <div class="prediction-message-alt">
                        <strong>Prediction:</strong> {message['content']}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Add gap between messages
                if i < len(st.session_state.chat_history) - 1:
                    st.markdown("<div class='message-gap'></div>", unsafe_allow_html=True)

        # Input from user
        if not st.session_state.waiting_for_follow_up:
            symptoms = st.text_area("Describe your symptoms here:")
            
            if st.button("Start Diagnosis"):
                if symptoms:
                    # Add user message to chat
                    st.session_state.chat_history.append({
                        'type': 'user',
                        'content': symptoms
                    })
                    
                    # Get initial symptoms
                    matched_symptoms = gen.find_symptoms(symptoms, gen.symptoms_classes)
                    st.session_state.current_symptoms = matched_symptoms
                    
                    # Get top predictions
                    top_predictions = get_top_predictions(symptoms)
                    
                    if not top_predictions:
                        st.session_state.chat_history.append({
                            'type': 'assistant',
                            'content': "I couldn't identify specific symptoms in your description. Please try describing your symptoms more clearly using common medical terms."
                        })
                    else:
                        # Generate follow-up questions
                        follow_up_questions = generate_follow_up_questions(top_predictions, matched_symptoms)
                        st.session_state.follow_up_questions = follow_up_questions
                        
                        # Add assistant response
                        response = "Based on your symptoms, I'd like to ask a few follow-up questions to better understand your condition:"
                        st.session_state.chat_history.append({
                            'type': 'assistant',
                            'content': response
                        })
                        
                        st.session_state.waiting_for_follow_up = True
                        st.rerun()
                else:
                    st.write("Please enter a description of your symptoms.")
        
        # Follow-up questions section
        if st.session_state.waiting_for_follow_up and st.session_state.follow_up_questions:
            st.write("### Follow-up Questions")
            
            follow_up_responses = {}
            
            for i, q_data in enumerate(st.session_state.follow_up_questions):
                # Add visual indicator for unique symptoms
                if q_data.get('unique', False):
                    st.write(f"**{q_data['question']}** 🎯 *(Unique symptoms to this disease)*")
                else:
                    st.write(f"**{q_data['question']}**")
                
                # Create checkboxes for symptoms
                symptom_responses = {}
                for symptom in q_data['symptoms']:
                    response = st.checkbox(f"Yes, I have {symptom}", key=f"symptom_{i}_{symptom}")
                    symptom_responses[symptom] = response
                
                follow_up_responses[q_data['disease']] = symptom_responses
                st.write("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Submit Follow-up Responses"):
                    # Collect all positive responses
                    additional_symptoms = []
                    for disease, responses in follow_up_responses.items():
                        for symptom, has_symptom in responses.items():
                            if has_symptom:
                                additional_symptoms.append(symptom)
                    
                    # Add follow-up response to chat
                    if additional_symptoms:
                        follow_up_text = f"Additional symptoms: {', '.join(additional_symptoms)}"
                        st.session_state.chat_history.append({
                            'type': 'user',
                            'content': follow_up_text
                        })
                    
                    # Update symptoms and get final prediction
                    all_symptoms = st.session_state.current_symptoms + additional_symptoms
                    final_result = gen.give_predicted_result(" ".join(all_symptoms))
                    
                    if final_result and final_result['confidence_score'] >= 0.35:
                        prediction_text = f"**Final Prediction:** {final_result['predicted_disease']}\n"
                        prediction_text += f"**Confidence:** {final_result['confidence_score'] * 100:.2f}%\n"
                        prediction_text += f"**Definition:** {final_result['description']}\n\n"
                        prediction_text += "**Recommendations:**\n"
                        for rec in final_result['recommendations']:
                            prediction_text += f"• {rec}"
                        
                        st.session_state.chat_history.append({
                            'type': 'prediction',
                            'content': prediction_text
                        })
                    else:
                        st.session_state.chat_history.append({
                            'type': 'assistant',
                            'content': "Based on all the information provided, I couldn't make a confident prediction. Please consult with a healthcare professional for a proper diagnosis."
                        })
                    
                    # Don't reset - let user continue conversation
                    st.session_state.waiting_for_follow_up = False
                    st.session_state.follow_up_questions = []
                    st.rerun()
            
            with col2:
                if st.button("Skip Follow-up Questions"):
                    # Get prediction with current symptoms only
                    result = gen.give_predicted_result(" ".join(st.session_state.current_symptoms))
                    
                    if result and result['confidence_score'] >= 0.35:
                        prediction_text = f"**Prediction:** {result['predicted_disease']}\n"
                        prediction_text += f"**Confidence:** {result['confidence_score'] * 100:.2f}%\n"
                        prediction_text += f"**Definition:** {result['description']}\n\n"
                        prediction_text += "**Recommendations:**\n"
                        for rec in result['recommendations']:
                            prediction_text += f"• {rec}"
                        
                        st.session_state.chat_history.append({
                            'type': 'prediction',
                            'content': prediction_text
                        })
                    else:
                        st.session_state.chat_history.append({
                            'type': 'assistant',
                            'content': "Based on the symptoms provided, I couldn't make a confident prediction. Please consult with a healthcare professional for a proper diagnosis."
                        })
                    
                    # Don't reset - let user continue conversation
                    st.session_state.waiting_for_follow_up = False
                    st.session_state.follow_up_questions = []
                    st.rerun()
        
        # Clear conversation button
        if st.session_state.chat_history:
            if st.button("Start New Conversation"):
                st.session_state.chat_history = []
                st.session_state.current_symptoms = []
                st.session_state.follow_up_questions = []
                st.session_state.waiting_for_follow_up = False
                st.rerun()























    #Diabetes Prediction Page
    if selected == 'Diabetes Prediction':
        st.title('Diabetes Predictor')

        # Input fields for diabetes prediction
        pregnancies = st.number_input("Pregnancies", min_value=0, max_value=20, value=0, step=1)
        glucose = st.number_input("Glucose", min_value=0, max_value=200, value=0, step=1)
        blood_pressure = st.number_input("Blood Pressure", min_value=0, max_value=150, value=0, step=1)
        skin_thickness = st.number_input("Skin Thickness", min_value=0, max_value=100, value=0, step=1)
        insulin = st.number_input("Insulin", min_value=0, max_value=900, value=0, step=1)
        bmi = st.number_input("BMI", min_value=0.0, max_value=70.0, value=0.0, step=0.1)
        diabetes_pedigree_function = st.number_input("Diabetes Pedigree Function", min_value=0.0, max_value=2.5, value=0.0, step=0.01)
        age = st.number_input("Age", min_value=0, max_value=120, value=0, step=1)

        if st.button("Predict Diabetes"):
            if( [glucose,blood_pressure, skin_thickness, insulin, bmi, diabetes_pedigree_function, age]==[0,0,0,0,0.00,0.00,0]) :
                    st.write("Please enter details properly")

            else:
                # Get predictions from the diabetes model
                result = diab.give_diabetes_prediction([pregnancies, glucose, blood_pressure, skin_thickness, insulin, bmi, diabetes_pedigree_function, age])
                
                # Display the result
                st.write("### Prediction Result")
                st.write(f"Prediction: {result['predicted_class']}")
                st.write(f"Confidence: {result['confidence']} % &nbsp; &nbsp;&nbsp;&nbsp; **(This confidence score reflects the reliability of the prediction)**")


    #Skin Disease Prediction Page
    if selected == 'Skin Disease Prediction':

            st.title("Skin Disease Prediction")
            st.write("Upload an image for prediction")

            # File uploader widget
            uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

            if uploaded_file is not None:

                # Display the uploaded image
                image = Image.open(uploaded_file)
                st.image(image, caption='Uploaded Image.', width=400)

                # Predict button
                if st.button('Predict'):
                        # Make prediction on the uploaded image
                        prediction = skin.give_skin_diseases_prediction(uploaded_file)

                        st.write(f"Prediction: {prediction['predicted_class']}")
                        st.write(f"Confidence: {prediction['confidence']} %&nbsp; &nbsp;&nbsp;&nbsp; **(This confidence score reflects the reliability of the prediction)**")


if __name__ == '__main__':
    main()