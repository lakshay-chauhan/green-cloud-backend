from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from simulation import simulate

app = FastAPI()

# ✅ CORS FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all (for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Green Cloud Simulation API Running"}

@app.post("/run-simulation")
def run_simulation():
    return simulate({})