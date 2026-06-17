import os
import threading
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from src.database.connection import init_db
from src.api.routes import router
from src.simulator.generator import BackgroundSimulator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("RRM.API")

# Load configuration
load_dotenv()
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", 8000))

# Global handle for background simulator
app_simulator = None
simulator_thread = None
stop_simulator_event = threading.Event()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages API startup and shutdown lifecycles.
    Bootstraps the simulator thread on start, and cleans it up on shutdown.
    """
    global app_simulator, simulator_thread, stop_simulator_event
    logger.info("Initializing database and starting background simulator...")
    
    # Initialize DB schemas
    init_db()

    # Start Background Telemetry Simulator
    app_simulator = BackgroundSimulator()
    stop_simulator_event.clear()
    
    simulator_thread = threading.Thread(
        target=app_simulator.run_loop,
        args=(stop_simulator_event,),
        daemon=True,
        name="SimulatorWorker"
    )
    simulator_thread.start()
    logger.info("Background simulator worker thread started.")
    
    yield  # Serve API requests
    
    # Shutdown
    logger.info("Stopping background simulator thread...")
    stop_simulator_event.set()
    if simulator_thread:
        simulator_thread.join(timeout=5)
    logger.info("Shutdown lifecycle complete.")


app = FastAPI(
    title="AI-Assisted WiFi Radio Resource Management (RRM) API",
    description="REST backend that serves simulated AP telemetry, change detection alerts, and optimization recommendations.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for the Streamlit dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow dashboard access from any client host
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root route
@app.get("/")
def read_root():
    return {
        "project": "AI-Assisted Client-Aware WiFi RRM Prototype",
        "docs_url": "/docs",
        "endpoints": ["/telemetry", "/alerts", "/recommendations", "/ap-status"]
    }

# Register routing
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=True)
