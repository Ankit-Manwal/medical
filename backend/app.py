import os
import sys
import json
import tempfile
from typing import List, Dict, Any

from flask import Flask, jsonify, request
from dotenv import load_dotenv
# Removed unused import - give_description is imported from the local module
from openai import OpenAI
from flask_cors import CORS


def create_app() -> Flask:
    app = Flask(__name__)

    # Enable CORS for local dev (Vite default port)
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}})

    # Prefer local copy inside backend for independence
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    # Lazy imports after path setup (match new folder names)
    from general_symptom_based_detection import general_conditions_backendfunction as gen  # type: ignore
    from diabetes.diabetes_backendfunction import give_diabetes_prediction  # type: ignore
    from skin_diseases.skin_diseases_backendfunction import give_skin_diseases_prediction  # type: ignore

    # Load environment (.env at backend root)
    load_dotenv(os.path.join(backend_dir, '.env'))
    openai_api_key = os.getenv('OPENAI_API_KEY', '')

    # Initialize OpenAI client via OpenRouter when key provided
    openai_client = None
    if openai_api_key:
        try:
            openai_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=openai_api_key)
        except Exception:
            openai_client = None

    # Preload model details and available tests
    model_detail_path = os.path.join(backend_dir, 'general_symptom_based_detection', 'model_detail.json')
    with open(model_detail_path, 'r', encoding='utf-8') as f:
        model_detail = json.load(f)

    condition_specific_symptoms: Dict[str, List[str]] = model_detail.get('condition_specific_symptoms', {})




    uniqueness_rarity_percent = gen.get_frequency_uniqueness_rarity_percent(condition_specific_symptoms)
    #     {
    #     symptom: {
    #         "frequency_percent": float,  # (count / total diseases) * 100
    #         "rarity_percent": float,     # 100 - frequency_percent
    #         "uniqueness": float          # 100 if unique to one disease else 50
    #     }
    # }


    all_models_file = os.path.join(backend_dir, 'resources', 'all_disease_specific_model_details.json')
    with open(all_models_file, 'r', encoding='utf-8') as f:
        disease_models = json.load(f)

    available_tests: Dict[str, str] = disease_models.get('available_tests', {})

    # Build LLM system prompt context
    known_symptoms_list = list(model_detail.get('all_symptoms', []))
    known_tests_list = list(available_tests.keys())
    known_symptoms_str = ", ".join(known_symptoms_list)
    known_tests_str = ", ".join(known_tests_list)

    system_prompt = f"""
You are a medical text parser. For any user message, return only a valid JSON object with these keys:

{{
    "symptoms_to_add": "Symptoms in user's text that exactly match or are medically related to items in the KNOWN_SYMPTOMS list (include indirect/associated symptoms). Empty string if none.",
    "symptoms_to_removed": "Symptoms from KNOWN_SYMPTOMS explicitly stated as not present. Empty string if none.",
    "specific_tests_to_run": "Specific medical tests mentioned or implied. If similar to a test in KNOWN_TESTS, use that exact name. Only add a brand-new test if no match exists in KNOWN_TESTS.",
    "specific_diseases_detail": "If the user requests disease info, give a short description, likely causes, and precautions. Empty string if none.",
    "invalid_input": "If unrelated to symptoms/tests/diseases, explain briefly. Else empty string.",
}}

KNOWN_SYMPTOMS = [{known_symptoms_str}]
KNOWN_TESTS = [{known_tests_str}]

Rules:
- Always return all keys exactly as shown, never omit.
- Use exact matches or strong medical similarity to link to KNOWN_SYMPTOMS and KNOWN_TESTS.
- If user mentions a test directly OR implies a test from possible disease history, add it to 'specific_tests_to_run' and make it top priority in 'priority_order'.
- Do not add explanations outside JSON.
- If multiple items exist for a field, separate with commas.
"""

    # Import LLM parsing helpers
    from general_symptom_based_detection.llm_resource.llm_reply_functions import (
        parse_llm_reply_to_dict, normalize_llm_reply,
    )  # type: ignore

    @app.get('/api/health')
    def health() -> Any:
        return jsonify({"status": "ok"})

    @app.get('/api/tests/available')
    def get_available_tests() -> Any:
        return jsonify({"available_tests": available_tests})

    @app.post('/api/llm/parse')
    def llm_parse() -> Any:
        print(f"\n\n*************************('/api/llm/parse')***************************************************************************")
        data = request.get_json(silent=True) or {}
        user_message = str(data.get('message', '')).strip()

        # 🖥️ Debug: log incoming request
        print(f"[LLM_PARSE] Received user message: {user_message}")

        if not user_message:
            print("[LLM_PARSE] Error: No message provided")
            return jsonify({"error": "message is required"}), 400

        if openai_client is None:
            print("[LLM_PARSE] Error: OpenAI client not configured")
            return jsonify({"error": "LLM client not configured. Set OPENAI_API_KEY in .env"}), 500

        try:
            # 🖥️ Debug: log LLM request
            print("[LLM_PARSE] Sending to LLM...")

            completion = openai_client.chat.completions.create(
                model="openai/gpt-oss-20b:free",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
            ai_reply = completion.choices[0].message.content or ""

            # 🖥️ Debug: log LLM response
            print(f"[LLM_PARSE] Raw AI reply: {ai_reply}")

        except Exception as e:
            print(f"[LLM_PARSE] LLM call failed: {str(e)}")
            return jsonify({"error": f"LLM call failed: {str(e)}"}), 502

        # Normalize reply to strict schema
        raw = parse_llm_reply_to_dict(ai_reply)
        normalized = normalize_llm_reply(raw, known_symptoms_list, known_tests_list)

        # 🖥️ Debug: log normalized response
        print(f"[LLM_PARSE] Parsed raw: {raw}")
        print(f"[LLM_PARSE] Normalized: {normalized}")

        return jsonify({"raw": raw, "normalized": normalized})
# {
#   "raw": {
#     "symptoms_to_add": "high_fever",
#     "symptoms_to_removed": "",
#     "specific_tests_to_run": "",
#     "specific_diseases_detail": "",
#     "invalid_input": ""
#   },
#   "normalized": {
#     "symptoms_to_add": ["high_fever"],
#     "symptoms_to_removed": [],
#     "specific_tests_to_run": [],
#     "specific_diseases_detail": [],
#     "invalid_input": "",
#   }
# }



    @app.post('/api/general/top_predictions')
    def top_predictions() -> Any:
        data = request.get_json(silent=True) or {}
        symptoms_text = str(data.get('symptoms', '')).strip()
        if not symptoms_text:
            print("[TOP_PREDICTIONS] Error: No symptoms provided")
            return jsonify({"error": "symptoms is required"}), 400
        preds = gen.give_top_predictions(symptoms_text)
        print(f"\n\n[TOP_PREDICTIONS] For symptoms: {symptoms_text}, Predictions: {preds}\n\n")
        return jsonify({"predictions": preds})
#     [
#     {"disease": "Flu", "confidence": 0.82},
#     {"disease": "Common Cold", "confidence": 0.10},
#     {"disease": "COVID-19", "confidence": 0.05}
# ]



    @app.post('/api/general/predict')
    def predict_general() -> Any:
        data = request.get_json(silent=True) or {}
        symptoms_text = str(data.get('symptoms', '')).strip()
        if not symptoms_text:
            return jsonify({"error": "symptoms is required"}), 400
        result = gen.give_predicted_result(symptoms_text)
        # Enrich with description and recommendations if not already present
        if result and 'description' not in result:
            result['description'] = gen.give_description(result.get('predicted_disease', ''))
        if result and 'recommendations' not in result:
            result['recommendations'] = gen.give_recommendation(result.get('predicted_disease', ''))
        # Suggest test if available
        suggested_test = None
        disease_name = result.get('predicted_disease') if isinstance(result, dict) else None
        if disease_name and disease_name in available_tests:
            suggested_test = {
                'disease': disease_name,
                'model': available_tests[disease_name],
                'test_name': disease_name,
            }
        return jsonify({"result": result, "suggested_test": suggested_test})




    @app.post('/api/general/disease_info')
    def give_disease_info() -> Any:
        data = request.get_json(silent=True) or {}
        diseases = data.get('diseases', [])

        if not isinstance(diseases, list) or not diseases:
            return jsonify({"error": "diseases must be a non-empty list"}), 400

        # Get details for all diseases
        results = gen.get_disease_details(diseases)

        # Suggest tests if available
        suggested_tests = []
        for d in diseases:
            if d in available_tests:
                suggested_tests.append({
                    "disease": d,
                    "model": available_tests[d],
                    "test_name": d,
                })

        return jsonify({
            "results": results,
            "suggested_tests": suggested_tests
        })

# {
#   "results": [
#     {
#       "disease": "Flu",
#       "description": "Flu is a viral infection...",
#       "recommendations": ["Rest", "Drink fluids", "Consult a doctor"]
#     },
#     {
#       "disease": "Diabetes",
#       "description": "A condition with high sugar levels.",
#       "recommendations": ["Exercise daily", "Monitor blood sugar"]
#     }
#   ],
#   "suggested_tests": [
#     {
#       "disease": "Flu",
#       "model": "flu_test_model",
#       "test_name": "Flu"
#     },
#     {
#       "disease": "Diabetes",
#       "model": "diabetes_test_model",
#       "test_name": "Diabetes"
#     }
#   ]
# }




    @app.post('/api/general/followup')
    def generate_followup() -> Any:
        print(f"\n\n********************************FOLLOWUP***************************************************************************************************")
        data = request.get_json(silent=True) or {}
        print("\n[FOLLOWUP] Incoming request:", data)

        current_symptoms = set(data.get('current_symptoms', []) or [])
        symptoms_removed = set(data.get('symptoms_removed', []) or [])

        print(f"[FOLLOWUP] Current symptoms: {current_symptoms}")
        print(f"[FOLLOWUP] Removed symptoms: {symptoms_removed}")

        # Generate top predictions
        top_preds = gen.give_top_predictions(" ".join(list(current_symptoms)))
        print(f"[FOLLOWUP] Top predictions: {top_preds}")

        # Generate follow-up questions
        questions = gen.generate_follow_up_questions_from_all(
            all_predictions=top_preds,
            current_symptoms=current_symptoms,
            frequency_uniqueness_rarity_percent=uniqueness_rarity_percent,
            symptoms_removed=symptoms_removed,
            max_per_disease=int(data.get('max_per_disease', 3)),
            max_total=int(data.get('max_total', 10)),
        )
#         [
#     {
#         "disease": "Flu",
#         "symptoms": ["muscle pain", "chills"],
#         "question": "For Flu (confidence: 0.82%), do you have: muscle pain, chills?",
#         "confidence": 0.82
#     },
#     ...
# ]
        print(f"[FOLLOWUP] Generated questions: {questions}\n\n\n")
        return jsonify({"follow_up_questions": questions})










    @app.post('/api/diabetes/predict')
    def diabetes_predict() -> Any:
        data = request.get_json(silent=True) or {}
        print(f"\n\n*************************('/api/diabetes/predict')***************************************************************************")
        print(f"[DIABETES_PREDICT] Incoming request data: {data}")
        try:
            values = [
                float(data['pregnancies']),
                float(data['glucose']),
                float(data['blood_pressure']),
                float(data['skin_thickness']),
                float(data['insulin']),
                float(data['bmi']),
                float(data['diabetes_pedigree_function']),
                float(data['age']),
            ]
        except Exception:
            return jsonify({"error": "Invalid or missing diabetes parameters"}), 400
        result = give_diabetes_prediction(values)
        return jsonify(result)

    @app.post('/api/skin/predict')
    def skin_predict() -> Any:
        print(f"\n\n*************************('/api/skin/predict')***************************************************************************") 
        if 'file' not in request.files:
            return jsonify({"error": "file is required"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "empty filename"}), 400
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1] or '.png') as tmp:
                file.save(tmp)
                tmp_path = tmp.name
            result = give_skin_diseases_prediction(tmp_path)
            print(f"\n\n\n[SKIN_PREDICT] Prediction result: {result}")
            return jsonify(result)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=True)


