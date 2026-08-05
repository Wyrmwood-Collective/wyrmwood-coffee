import subprocess
from pathlib import Path

from fastapi import FastAPI

app = FastAPI()


def dev():
    subprocess.run(["fastapi", "dev", str(Path(__file__))])


@app.get("/")
def root():
    return {"message": "Hello World!"}
