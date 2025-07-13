import logger
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn

from monitor import ProcessMonitor
from logger import logger


monitor = ProcessMonitor("config.json")
templates = Jinja2Templates(directory="templates")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting ProcessMonitor via FastAPI lifespan...")
    monitor.start()
    yield
    monitor.stop()
    logger.info("Stopped ProcessMonitor via FastAPI lifespan.")

app = FastAPI(lifespan=lifespan)

class ProcessName(BaseModel):
    name: str

@app.post("/add_process")
async def add_process(proc: ProcessName):
    proc_name = proc.name.lower()
    logger.info(f"Received request to add process '{proc_name}'")
    with monitor.lock:
        if proc_name not in monitor.processes_to_monitor:
            monitor.processes_to_monitor.append(proc_name)
            logger.info(f"Process '{proc_name}' added to monitor list.")
            return {"message": f"Process '{proc_name}' added to monitoring list."}
        else:
            logger.info(f"Process '{proc_name}' is already monitored.")
            return {"message": f"Process '{proc_name}' is already being monitored."}

@app.delete("/delete_process")
async def delete_process(proc: ProcessName):
    proc_name = proc.name.lower()
    logger.info(f"Received request to delete process '{proc_name}'")
    with monitor.lock:
        if proc_name in monitor.processes_to_monitor:
            monitor.processes_to_monitor.remove(proc_name)
            if proc_name in monitor.status:
                del monitor.status[proc_name]
            logger.info(f"Process '{proc_name}' removed from monitor list.")
            return {"message": f"Process '{proc_name}' removed from monitoring list."}
        else:
            logger.info(f"Process '{proc_name}' was not found in monitor list.")
            return {"message": f"Process '{proc_name}' is not being monitored."}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    logger.info("Rendering dashboard")
    status = monitor.get_status()
    return templates.TemplateResponse("dashboard.html", {"request": request, "status": status})

if __name__ == "__main__":
    logger.info("Starting FastAPI server...")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
