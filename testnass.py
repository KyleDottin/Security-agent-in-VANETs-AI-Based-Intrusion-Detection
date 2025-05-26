from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Welcome to the Simulation API"}

@app.post("/create_vehicle")
def create_vehicle():
    return {"status": "vehicle created"}

@app.post("/create_agent")
def create_agent():
    return {"status": "agent created"}

@app.post("/report_attack")
def report_attack():
    return {"status": "attack reported"}

@app.post("/simulate_attack")
def simulate_attack():
    return {"status": "attack simulated"}
