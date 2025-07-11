from fastapi import FastAPI
from fastapi.responses import HTMLResponse
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
            table { border-collapse: collapse; margin: 0 auto; width: 50%; }
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
            </tr>
    """
    for proc, is_running in status.items():
        status_str = "RUNNING" if is_running else "NOT RUNNING"
        status_class = "running" if is_running else "not-running"
        html += f"""
            <tr>
                <td>{proc}</td>
                <td class="{status_class}">{status_str}</td>
            </tr>
        """
    html += """
        </table>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
