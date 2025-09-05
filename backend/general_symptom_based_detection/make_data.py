import pandas as pd
import json
import os
import sys

# Get the parent directory of the current script
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
sys.path.insert(0, parent_dir)

def load_dataset():
    """Load the main dataset"""
    dataset_path = os.path.join(parent_dir, 'dataset/dataset.csv')
    return pd.read_csv(dataset_path)



def extract_disease_symptoms(df_dataset):
    """Extract symptoms for each disease from the dataset"""
    condition_specific_symptoms = {}
    
    # Get unique diseases
    unique_diseases = df_dataset['Disease'].unique()
    
    for disease in unique_diseases:
        # Get all rows for this disease
        disease_data = df_dataset[df_dataset['Disease'] == disease]
        
        # Set to store all unique symptoms for this disease
        disease_symptoms = set()
        
        # Iterate through all rows for this disease
        for _, row in disease_data.iterrows():
            # Get all symptoms from the row (skip the Disease column)
            symptoms = [s.strip() for s in row[1:] if pd.notna(s) and s.strip()]
            disease_symptoms.update(symptoms)
        
        # Convert set to sorted list
        condition_specific_symptoms[disease] = sorted(list(disease_symptoms))
    
    return condition_specific_symptoms

def extract_all_symptoms(df_dataset):
    """Extract all unique symptoms from the dataset"""
    all_symptoms = set()
    
    for _, row in df_dataset.iterrows():
        symptoms = [s.strip() for s in row[1:] if pd.notna(s) and s.strip()]
        all_symptoms.update(symptoms)
    
    return sorted(list(all_symptoms))



def create_model_detail_data():
    """Create model_detail.json compatible data file"""
    print("Loading datasets...")
    
    # Load main dataset
    df_dataset = load_dataset()
    
    print("Extracting disease symptoms...")
    condition_specific_symptoms = extract_disease_symptoms(df_dataset)
    
    print("Extracting all symptoms...")
    all_symptoms = extract_all_symptoms(df_dataset)
    
    # Create model_detail.json compatible structure
    model_detail_data = {
        "model_path": "general_conditions_model.h5",
        "diseases_classes": sorted(list(condition_specific_symptoms.keys())),
        "all_symptoms": all_symptoms,
        "condition_specific_symptoms": condition_specific_symptoms
    }
    
    return model_detail_data

def save_data(data, filename="model_detail.json"):
    """Save the data to a JSON file"""
    output_path = os.path.join(parent_dir, filename)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    print(f"Data saved to: {output_path}")
    return output_path

def print_summary(data):
    """Print a summary of the created data"""
    print("\n" + "="*60)
    print("MODEL DETAIL DATA SUMMARY")
    print("="*60)
    
    print(f"Model Path: {data['model_path']}")
    print(f"Total Diseases: {len(data['diseases_classes'])}")
    print(f"Total Symptoms: {len(data['all_symptoms'])}")
    
    print("\nDISEASES:")
    print("-" * 40)
    for i, disease in enumerate(data['diseases_classes'], 1):
        symptom_count = len(data['condition_specific_symptoms'][disease])
        print(f"{i:2d}. {disease} ({symptom_count} symptoms)")
    
    print(f"\nSYMPTOMS:")
    print("-" * 40)
    print(f"Total unique symptoms: {len(data['all_symptoms'])}")
    
    # Show some sample symptoms
    print("Sample symptoms:")
    for i, symptom in enumerate(data['all_symptoms'][:10], 1):
        print(f"  {i}. {symptom}")
    
    if len(data['all_symptoms']) > 10:
        print(f"  ... and {len(data['all_symptoms']) - 10} more symptoms")

def main():
    """Main function to create model_detail.json data"""
    print("Creating model_detail.json data...")
    print("="*60)
    
    try:
        # Create model detail data
        data = create_model_detail_data()
        
        # Save to file (will overwrite if exists)
        output_path = save_data(data)
        
        # Print summary
        print_summary(data)
        
        print(f"\n✅ Successfully created model_detail.json!")
        print(f"📁 File saved as: {output_path}")
        print("🔄 File will be overwritten if it already exists")
        
    except Exception as e:
        print(f"❌ Error creating data: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 