import os
import re
import json
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from simulation import simulate

app = FastAPI(title="Green Cloud & Code Analyzer API")

# ✅ CORS FIX: Allows your Vercel frontend to communicate with this Render backend
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
    Analyze the following code for complexity.
    1. Estimate CPU Cycles (T) for n=1000.
    2. Estimate Memory usage in Bytes (S).
    
    EXPECTED JSON FORMAT:
    {{"T": 5000, "S": 256}}

    CODE:
    {payload.code}
    
    Return ONLY the raw JSON. No markdown, no explanation.
    """
    
    try:
        response = model.generate_content(prompt)
        # Use regex to extract JSON in case the model adds extra text
        json_match = re.search(r"\{.*\}", response.text, re.DOTALL)
        if not json_match:
            raise ValueError("Invalid AI response format")
            
        data = json.loads(json_match.group())
        T, S = float(data.get("T", 5000)), float(data.get("S", 256))

        # Calculate Environmental Impact
        energy_j = (0.8e-9 * T) + (1.2e-9 * S)
        water_ml = (energy_j / 3600000) * 1.8 * 1000
        
        # Rating Logic
        impact_score = (energy_j * 10**5) + (water_ml * 50)
        grade = "A+ (Efficient)" if impact_score < 10 else "D (Resource Heavy)"

        return {
            "environmental_impact": {
                "energy_joules": energy_j,
                "water_usage_ml": water_ml
            },
            "sustainability_rating": grade,
            "parameters": {"T": T, "S": S}
        }
    except Exception as e:
        print(f"Analysis Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run-simulation")
def run_simulation_endpoint(payload: dict):
    try:
        return simulate(payload)
    except Exception as e:
        print(f"Simulation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)