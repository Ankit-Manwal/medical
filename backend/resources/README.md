# Medical Model Runners

This directory contains modular model runners for executing specific medical model tests with Streamlit-compatible parameter setup and execution.

## Structure

```
specific_medical_model/
├── __init__.py                           # Package initialization
├── all_disease_specific_model_details.json  # Model configuration
├── model_runner.py                       # Main model runner
├── skin_diseases_model_runner.py         # Skin diseases model runner
├── diabetes_model_runner.py              # Diabetes model runner
├── test_runners.py                       # Test script
└── README.md                             # This file
```

## Files Overview

### `all_disease_specific_model_details.json`
Configuration file that defines:
- Available tests mapping (disease name → model name)
- Model details (parameters, backend functions, etc.)
- Test examples and expected outputs

### `model_runner.py`
Main module providing unified interface for:
- Loading model configuration
- Setting up parameters for any model
- Running tests with proper error handling
- Displaying results

### `skin_diseases_model_runner.py`
Specialized runner for skin disease classification:
- Image upload interface
- Parameter setup (target size, scale factor)
- Integration with skin diseases backend
- Test image path utilities

### `diabetes_model_runner.py`
Specialized runner for diabetes risk assessment:
- Numeric parameter inputs (glucose, blood pressure, etc.)
- Parameter validation and ranges
- Integration with diabetes backend
- Sample data utilities

## Usage

### Basic Usage

```python
from general_conditions.specific_medical_model import (
    setup_model_parameters,
    run_model_test,
    get_available_tests
)

# Get available tests
available_tests = get_available_tests()

# Setup parameters for a model
parameters = setup_model_parameters('Skin Diseases')

# Run the test
result = run_model_test('Skin Diseases', parameters)
```

### In Streamlit Frontend

The model runners are integrated into `streamlit_app/front.py`:

1. When LLM suggests specific tests, the system maps them to available models
2. Users can consent to run the tests
3. The system automatically sets up parameters and runs the tests
4. Results are displayed in the chat interface

### Testing

Run the test script to verify everything works:

```bash
cd general_conditions/specific_medical_model
python test_runners.py
```

## Model Integration

### Adding New Models

To add a new model:

1. Create a new runner file (e.g., `new_model_runner.py`)
2. Implement the required functions:
   - `setup_new_model_parameters()` - Streamlit UI for parameters
   - `run_new_model_test(parameters)` - Execute the model
3. Update `model_runner.py` to include the new model
4. Update `__init__.py` to export the new functions
5. Add model configuration to `all_disease_specific_model_details.json`

### Required Functions

Each model runner should provide:

```python
def setup_model_parameters():
    """Setup Streamlit UI for model parameters"""
    # Return dict with parameters
    
def run_model_test(parameters):
    """Execute model with given parameters"""
    # Return dict with results:
    # {
    #     'success': bool,
    #     'predicted_disease': str,
    #     'confidence_score': float,
    #     'error': str (if success=False)
    # }
```

## Configuration

The `all_disease_specific_model_details.json` file structure:

```json
{
  "available_tests": {
    "Disease Name": "Model Name"
  },
  "models": {
    "Model Name": {
      "category": "model_type",
      "model_path": "path/to/model",
      "backend_function": "path/to/backend::function",
      "parameters": [...],
      "test": {
        "input": {...},
        "expected_output_keys": [...]
      }
    }
  }
}
```

## Error Handling

All model runners include comprehensive error handling:
- Parameter validation
- Model loading errors
- Execution errors
- Result formatting errors

Errors are returned in a consistent format for display in the UI.

## Dependencies

- Streamlit
- PIL (for image processing)
- NumPy
- TensorFlow (for skin diseases model)
- Scikit-learn (for diabetes model)

## Notes

- All paths are relative to the project root
- Model runners automatically handle path resolution
- Results are normalized to `predicted_disease` and `confidence_score` format
- Backend functions are expected to return `predicted_class` and `confidence` which are mapped to the expected format
