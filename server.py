from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn

from monitor import ProcessMonitor

# Initialize the process monitor with configuration from file
monitor = ProcessMonitor("config.json")
# Initialize Jinja2 template renderer (expects templates in 'templates/' directory)
templates = Jinja2Templates(directory="templates")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan handler: starts and stops the process monitor when the app runs.
    """
    monitor.start()  # Start monitoring in background
    yield
    monitor.stop()  # Stop monitoring when app shuts down

# Create FastAPI app with lifespan context
app = FastAPI(lifespan=lifespan)

class ProcessName(BaseModel):
    """
    Data model for incoming process name payloads.
    """
    name: str

@app.post("/add_process")
async def add_process(proc: ProcessName):
    """
    API endpoint to add a process name to the monitoring list.
    """
    proc_name = proc.name.lower()
    with monitor.lock:
        if proc_name not in monitor.processes_to_monitor:
            monitor.processes_to_monitor.append(proc_name)
            return {"message": f"Process '{proc_name}' added to monitoring list."}
        else:
            return {"message": f"Process '{proc_name}' is already being monitored."}

@app.delete("/delete_process")
async def delete_process(proc: ProcessName):
    """
    API endpoint to remove a process name from the monitoring list.
    """
    proc_name = proc.name.lower()
    with monitor.lock:
        if proc_name in monitor.processes_to_monitor:
            monitor.processes_to_monitor.remove(proc_name)
            # Also remove its current status if present
            if proc_name in monitor.status:
                del monitor.status[proc_name]
            return {"message": f"Process '{proc_name}' removed from monitoring list."}
        else:
            return {"message": f"Process '{proc_name}' is not being monitored."}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Render the dashboard HTML with current process statuses.
    """
    status = monitor.get_status()
    return templates.TemplateResponse("dashboard.html", {"request": request, "status": status})

if __name__ == "__main__":
    # Run the FastAPI app with auto-reload enabled for development
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
