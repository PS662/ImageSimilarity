import os
from typing import List

from fastapi import FastAPI, UploadFile, Form, BackgroundTasks, APIRouter
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from starlette.requests import Request

from celery.result import AsyncResult

from .tasks import search_vector, add_vector
import asyncio


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/temp_catalogue", StaticFiles(directory="temp_catalogue"), name="temp_catalogue")
app.mount("/config", StaticFiles(directory="config"), name="config")

templates = Jinja2Templates(directory="templates")
router = APIRouter()

@app.get("/")
async def read_root(request: Request):  # Use Request from starlette
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})

# FIXME: Add base64 encoded search
@app.post("/search_with_image")
async def search_with_image(file: UploadFile,
                            model_id: str = Form(None)):
    print(f"Received model_id: {model_id}")  # Debug line
    if not model_id:
        raise HTTPException(status_code=400, detail="model_id is required")
    temp_path = f"temp/{file.filename}"
    try:
        with open(temp_path, "wb") as f:
            f.write(file.file.read())
        task = search_vector.delay(temp_path, model_id)
        return {"task_id": task.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task failed: {str(e)}")


# FIXME: Add base64 encoded upload, progress bar UI
@router.post("/upload_catalogue")
async def upload_catalogue(
    files: List[UploadFile],
    model_id: str = Form(None)):
    try:
        print(f"Files received: {[file.filename for file in files]}")
        print(f"Model ID: {model_id}")

        temp_folder = "temp_catalogue"
        os.makedirs(temp_folder, exist_ok=True)
        print(f"Temporary folder created: {temp_folder}")

        file_paths = []
        for file in files:
            filename = os.path.basename(file.filename)
            temp_path = os.path.join(temp_folder, filename)
            with open(temp_path, "wb") as f:
                f.write(await file.read())
            file_paths.append(temp_path)
            print(f"File saved: {temp_path}")

        task = add_vector.delay(temp_folder, model_id)
        print(f"Task scheduled with ID: {task.id}")
        return {"task_id": task.id}
    except Exception as e:
        print(f"Error in /upload_catalogue: {e}")
        raise HTTPException(status_code=500, detail=f"Task failed: {str(e)}")


@app.get("/get_task_status/{req_id}")
async def get_task_status(req_id: str):
    """Retrieve the status of a task."""
    task = AsyncResult(req_id)
    if task.state == "SUCCESS":
        return {"status": task.state, "result": task.result}
    else:
        return {"status": task.state}


@app.get("/poll_task_status/{req_id}")
async def poll_task_status(req_id: str, target_status: str = "SUCCESS", timeout: int = 30, retry_limit: int = 3):
    """Long-poll task status until the target status or timeout."""
    if not req_id or req_id == "undefined":
        raise HTTPException(status_code=400, detail="Invalid or missing task ID.")

    start_time = asyncio.get_event_loop().time()
    retries = 0

    while retries < retry_limit:
        task = AsyncResult(req_id)
        current_status = task.state

        if current_status == target_status:
            return {"status": task.state, "result": task.result}
        elif current_status == "FAILURE":
            return {"status": task.state, "result": str(task.info)}

        elapsed_time = asyncio.get_event_loop().time() - start_time
        if elapsed_time > timeout:
            retries += 1
            if retries >= retry_limit:
                return {"status": 408, "result": "Connection Timeout"}
            start_time = asyncio.get_event_loop().time()

        await asyncio.sleep(1)

    return {"status": "TIMEOUT", "result": "Task did not complete within the expected time."}
app.include_router(router)
