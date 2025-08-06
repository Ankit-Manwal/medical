import os
import pickle
import numpy as np

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

model_path = os.path.join(parent_dir, 'diabetes/diabetes_model.pkl')

model = pickle.load(open(model_path, "rb") )  

class_names=["No Diabetes","Diabetes"]

def give_diabetes_prediction(inp):
    predictions = model.predict_proba(np.array(inp).reshape(1,-1))
    predicted_class = class_names[np.argmax(predictions[0])]
    confidence = round(100 * (np.max(predictions[0])), 2)
    return {"predicted_class":predicted_class, "confidence":confidence}



# print(give_diabetes_prediction([ 12.   , 121.   ,  78.   ,  17.   ,   0.   ,  26.5  ,   0.259,
#         62.   ]))