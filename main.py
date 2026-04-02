import os
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from simulation import simulate

app = FastAPI(title="Green Cloud & Code Analyzer API")

# ✅ 1. GLOBAL CORS FIX
# This allows your Vercel frontend to communicate with this Render backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For extra security, replace "*" with your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 2. CONFIGURATION & MODELS
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"

if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
else:
    print("WARNING: GEMINI_API_KEY is not set. Analyzer features will be disabled.")

class CodePayload(BaseModel):
    code: str

# ✅ 3. ENDPOINTS

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Green Cloud Simulation & Analyzer API is running",
        "endpoints": ["/analyze", "/run-simulation"]
    }

@app.post("/analyze")
async def analyze_code(payload: CodePayload):
    """
    Analyzes code complexity using Gemini 2.5 Flash to determine 
    Environmental Impact before simulation.
    """
    if not API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Key not configured on server.")

    prompt = f"""
    Analyze the following code for complexity.
    1. Estimate CPU Cycles (T) for an input size n=1000.
    2. Estimate Memory usage in Bytes (S).
    
    EXPECTED JSON FORMAT:
    {{"T": 5000, "S": 256}}

    CODE:
    {payload.code}
    
    Return ONLY the raw JSON object. No markdown, no explanation.
    """
    
    try:
        response = model.generate_content(prompt)
        import re
        import json
        
        # Clean response to ensure only JSON is parsed
        json_match = re.search(r"\{.*\}", response.text, re.DOTALL)
        if not json_match:
            raise ValueError("Model failed to return valid JSON structure.")
            
        return json.loads(json_match.group())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run-simulation")
def run_simulation(payload: dict):
    """
    Runs the Cloud Simulation using the impact metrics 
    received from the React frontend.
    """
    try:
        # Passes the 'code_impact' (energy, rating) from React to simulation.py
        result = simulate(payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Use the PORT provided by Render or default to 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)