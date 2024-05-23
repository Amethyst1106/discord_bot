from threading import Thread
import os
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
	return {"message": "Server is Online."}

def start():
	uvicorn.run(app, host="0.0.0.0", port=os.environ["PORT"])

def server_thread():
	t = Thread(target=start)
	t.start()