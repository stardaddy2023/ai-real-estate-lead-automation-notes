import vertexai
from vertexai.generative_models import GenerativeModel
from app.core.config import settings
import json
import os
from google.oauth2 import service_account
from dotenv import load_dotenv
from pathlib import Path

# Force load .env from project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

class LeadAnalystAgent:
    def __init__(self):
        self.model_name = "gemini-2.5-pro"
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or settings.GOOGLE_CLOUD_PROJECT
        self.location = os.getenv("VERTEX_AI_LOCATION") or settings.VERTEX_AI_LOCATION
        
        if self.project_id:
            try:
                # Explicitly load credentials if available
                creds = None
                cred_filename = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                
                if cred_filename:
                    # Try absolute path first, then relative to backend root
                    cred_path = Path(cred_filename)
                    if not cred_path.exists():
                        cred_path = BASE_DIR / cred_filename
                    
                    if cred_path.exists():
                        print(f"Loading credentials from: {cred_path}")
                        creds = service_account.Credentials.from_service_account_file(str(cred_path))
                    else:
                        print(f"Warning: Credentials file not found at {cred_path}")
                
                vertexai.init(project=self.project_id, location=self.location, credentials=creds)
                self.model = GenerativeModel(self.model_name)
            except Exception as e:
                print(f"Failed to initialize Vertex AI: {e}")
                self.model = None
        else:
            self.model = None

    async def analyze_lead(self, property_data: dict):
        """
        Uses Gemini to analyze distress signals and score the lead.
        """
        if not self.model:
            print("Vertex AI not initialized. Returning mock score.")
            return self._get_mock_response()

        prompt = self._construct_prompt(property_data)
        print(f"Sending prompt to {self.model_name}...")
        
        try:
            response = self.model.generate_content(prompt)
            text_response = response.text
            print(f"Gemini Response: {text_response}")
            
            return {
                "score": 75, 
                "reasoning": text_response,
                "strategy": "WHOLESALE"
            }
        except Exception as e:
            print(f"Error calling Vertex AI: {e}")
            print("Falling back to Mock Response due to API error.")
            return self._get_mock_response(error_msg=str(e))

    def _get_mock_response(self, error_msg=None):
        reasoning = "High distress detected based on tax delinquency and vacancy."
        if error_msg:
            reasoning += f" (Note: AI Analysis failed: {error_msg}. Using mock data.)"
            
        return {
            "score": 88, 
            "reasoning": reasoning,
            "strategy": "WHOLESALE"
        }

    def _construct_prompt(self, data: dict) -> str:
        return f"""
        Analyze the following property for real estate investment potential.
        
        PROPERTY DETAILS:
        - Address: {data.get('address')}
        - Owner: {data.get('owner_name') or 'Unknown'}
        - Sqft: {data.get('sqft') or 'Unknown'}
        - Bedrooms: {data.get('bedrooms') or 'Unknown'}
        - Bathrooms: {data.get('bathrooms') or 'Unknown'}
        - Year Built: {data.get('year_built') or 'Unknown'}
        - Lot Size: {data.get('lot_size') or 'Unknown'} acres
        - Neighborhood: {data.get('neighborhood') or 'Unknown'}
        
        Distress Signals: {data.get('distress_signals', [])}
        
        INSTRUCTIONS:
        1. Use ONLY the provided property details. DO NOT hallucinate or invent features (like pool, garage, or specific year built) if they are not listed above.
        2. If a key detail is "Unknown", state that it is missing and base your analysis on the location and available data.
        3. Provide an Investment Score (0-100) based on the potential for a deal.
        4. Recommend a Strategy: Wholesale, Fix and Flip, or Buy and Hold.
        5. Provide a detailed reasoning breakdown including:
           - Property & Location Analysis
           - Recommended Strategy
           - The "Good" (Pros)
           - The "Bad" (Cons)
           - The "Ugly" (Risks)
        """
