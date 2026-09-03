from fastapi import FastAPI


app = FastAPI(
    title="Autonomous UAV Ground Control API",
    description="Backend API for the Autonomous UAV simulation and Ground Control Station.",
    version="1.0.0"
)


@app.get("/")
def root():

    return {
        "message": "Autonomous UAV API is running",
        "status": "online"
    }


@app.get("/api/health")
def health_check():

    return {
        "status": "healthy"
    }