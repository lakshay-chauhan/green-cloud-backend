import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from simulation import simulate

app = FastAPI(title="Green Cloud Simulation Backend")

# ✅ FIX: This resolves the "blocked by CORS policy" error
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows Vercel and local testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "online", "service": "Simulation Engine"}

@app.post("/run-simulation")
async def run_simulation_endpoint(payload: dict):
    try:
        # payload will contain the 'workloads' array from App.js
        result = simulate(payload)
        return result
    except Exception as e:
        print(f"SIMULATION CRASH: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))