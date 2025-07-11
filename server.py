from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn

from monitor import ProcessMonitor

monitor = ProcessMonitor("config.json")

@asynccontextmanager
async def lifespan(app: FastAPI):
    monitor.start()
    yield
    monitor.stop()

app = FastAPI(lifespan=lifespan)

class ProcessName(BaseModel):
    name: str


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    status = monitor.get_status()

    html = """
    <html>
    <head>
        <title>Process Monitor Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 20px; }
            h1 { text-align: center; }
            table { border-collapse: collapse; margin: 0 auto; width: 80%; }
            th, td { padding: 10px; border: 1px solid #ddd; text-align: center; }
            th { background-color: #333; color: #fff; }
            tr:nth-child(even) { background-color: #eee; }
            .running { color: green; font-weight: bold; }
            .not-running { color: red; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>Process Monitor Dashboard</h1>
        <table>
            <tr>
                <th>Process</th>
                <th>Status</th>
                <th>CPU %</th>
                <th>Memory (MB)</th>
                <th>Threads</th>
                <th>Lifetime (s)</th>
            </tr>
    """

    for proc, info in status.items():
        status_str = "RUNNING" if info['running'] else "NOT RUNNING"
        status_class = "running" if info['running'] else "not-running"
        html += f"""
            <tr>
                <td>{proc}</td>
                <td class="{status_class}">{status_str}</td>
                <td>{info['cpu_percent']:.1f}</td>
                <td>{info['memory_mb']:.2f}</td>
                <td>{info['num_threads']}</td>
                <td>{info['lifetime_sec']}</td>
            </tr>
        """

    html += """
        </table>
    </body>
    </html>
    """

    return HTMLResponse(content=html)


@app.post("/add_process")
async def add_process(proc: ProcessName):
    proc_name = proc.name.lower()
    with monitor.lock:
        if proc_name not in monitor.processes_to_monitor:
            monitor.processes_to_monitor.append(proc_name)
            return {"message": f"Process '{proc_name}' added to monitoring list."}
        else:
            return {"message": f"Process '{proc_name}' is already being monitored."}


@app.delete("/delete_process")
async def delete_process(proc: ProcessName):
    proc_name = proc.name.lower()
    with monitor.lock:
        if proc_name in monitor.processes_to_monitor:
            monitor.processes_to_monitor.remove(proc_name)

            if proc_name in monitor.status:
                del monitor.status[proc_name]
            return {"message": f"Process '{proc_name}' removed from monitoring list."}
        else:
            return {"message": f"Process '{proc_name}' is not being monitored."}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
