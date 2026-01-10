
import json
import math
import numpy as np

def test_sanitization():
    print("--- Testing NaN Sanitization ---")
    
    # Simulate data with various NaN types
    data = [
        {
            "normal": "value",
            "float_nan": float('nan'),
            "numpy_nan": np.nan,
            "nested": {
                "inner_nan": np.nan
            },
            "list_nan": [1, np.nan, 3]
        }
    ]
    
    print("Original Data:", data)
    
    # Current Sanitizer Logic (from scout.py)
    print("\nRunning Current Sanitizer...")
    try:
        for lead in data:
            for k, v in lead.items():
                if isinstance(v, float) and math.isnan(v):
                    lead[k] = None
                    
        print("Sanitized Data:", data)
        print("Serialization Check:", json.dumps(data))
        print("SUCCESS")
    except Exception as e:
        print(f"FAILURE: {e}")

    # Proposed Robust Sanitizer
    print("\nRunning Robust Sanitizer...")
    data_2 = [
        {
            "normal": "value",
            "float_nan": float('nan'),
            "numpy_nan": np.nan,
            "nested": {
                "inner_nan": np.nan
            },
            "list_nan": [1, np.nan, 3]
        }
    ]
    
    def sanitize(obj):
        if isinstance(obj, float) and math.isnan(obj):
            return None
        if isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [sanitize(x) for x in obj]
        return obj
        
    sanitized_2 = sanitize(data_2)
    print("Sanitized Data 2:", sanitized_2)
    print("Serialization Check 2:", json.dumps(sanitized_2))

if __name__ == "__main__":
    test_sanitization()
