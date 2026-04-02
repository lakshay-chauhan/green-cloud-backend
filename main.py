import os
import re
import json
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from simulation import simulate

app = FastAPI(title="Green Cloud & Code Analyzer API")

# ✅ FIXES THE CORS ERROR: Allows your Vercel frontend to talk to Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"

if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)

class CodePayload(BaseModel):
    code: str

@app.post("/analyze")
async def analyze_code(payload: CodePayload):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API Key not configured on server.")

    prompt = f"""
    Analyze the following code for complexity:
    1. Estimate CPU Cycles (T) for n=1000.
    2. Estimate Memory usage in Bytes (S).
    
    EXPECTED JSON FORMAT:
    {{"T": 5000, "S": 256}}

    CODE:
    {payload.code}
    
    Return ONLY raw JSON. No markdown, no explanation.
    """
    
    try:
        response = model.generate_content(prompt)
        json_match = re.search(r"\{.*\}", response.text, re.DOTALL)
        if not json_match:
            raise ValueError("Invalid AI response")
            
        data = json.loads(json_match.group())
        
        # Calculate environmental impact constants
        T, S = float(data.get("T", 0)), float(data.get("S", 0))
        energy_j = (0.8e-9 * T) + (1.2e-9 * S)
        water_ml = (energy_j / 3600000) * 1.8 * 1000
        
        # Assign Grade
        score = (energy_j * 10**5) + (water_ml * 50)
        grade = "A+ (Efficient)" if score < 10 else "D (Resource Heavy)"

        return {
            "environmental_impact": {"energy_joules": energy_j, "water_usage_ml": water_ml},
            "sustainability_rating": grade,
            "parameters": {"T": T, "S": S}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run-simulation")
def run_simulation(payload: dict):
    return simulate(payload)