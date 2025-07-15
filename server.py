from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn

from monitor import ProcessMonitor
from logger import logger

# Initialize the ProcessMonitor with settings from 'config.json'
monitor = ProcessMonitor("config.json")

# Set up template rendering for the dashboard
templates = Jinja2Templates(directory="templates")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager:
    Automatically starts the monitor when the app starts,
    and ensures a clean stop when the app shuts down.
    """
    logger.info("Starting ProcessMonitor via FastAPI lifespan...")
    monitor.start()  # Begin background monitoring
    yield  # App runs while suspended here
    monitor.stop()  # Stop monitoring on app shutdown
    logger.info("Stopped ProcessMonitor via FastAPI lifespan.")

# Initialize FastAPI app and wire the lifespan handler
app = FastAPI(lifespan=lifespan)

class ProcessName(BaseModel):
    """
    Pydantic schema to validate incoming JSON payloads with a process name.
    Example payload: { "name": "chrome" }
    """
    name: str

@app.post("/add_process")
async def add_process(proc: ProcessName):
    """
    Add a process name to the monitoring list.
    If it's already present, return a message indicating so.
    """
    proc_name = proc.name.lower()  # Normalize name to lowercase for consistency
    logger.info(f"Received request to add process '{proc_name}'")
    with monitor.lock:  # Ensure thread-safe update of the shared list
        if proc_name not in monitor.processes_to_monitor:
            monitor.processes_to_monitor.append(proc_name)
            logger.info(f"Process '{proc_name}' added to monitor list.")
            return {"message": f"Process '{proc_name}' added to monitoring list."}
        else:
            logger.info(f"Process '{proc_name}' is already monitored.")
            return {"message": f"Process '{proc_name}' is already being monitored."}

@app.delete("/delete_process")
async def delete_process(proc: ProcessName):
    """
    Remove a process name from the monitoring list.
    Also deletes its status entry if present.
    """
    proc_name = proc.name.lower()
    logger.info(f"Received request to delete process '{proc_name}'")
    with monitor.lock:  # Protect shared state with lock
        if proc_name in monitor.processes_to_monitor:
            monitor.processes_to_monitor.remove(proc_name)
            # Clean up status if it exists
            if proc_name in monitor.status:
                del monitor.status[proc_name]
            logger.info(f"Process '{proc_name}' removed from monitor list.")
            return {"message": f"Process '{proc_name}' removed from monitoring list."}
        else:
            logger.info(f"Process '{proc_name}' was not found in monitor list.")
            return {"message": f"Process '{proc_name}' is not being monitored."}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Render an HTML dashboard showing current monitored process statuses.
    """
    logger.info("Rendering dashboard")
    status = monitor.get_status()  # Get a snapshot of the current status dictionary
    return templates.TemplateResponse("dashboard.html", {"request": request, "status": status})

if __name__ == "__main__":
    # Run the FastAPI server with reload for dev convenience
    logger.info("Starting FastAPI server...")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
