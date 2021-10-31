from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional, List

class Car(BaseModel):
    make: str
    model: str
    year: int = Field(...,ge=1970,lt=2022)
    price: float
    engine: Optional[str] = "V4"
    autonomous: bool
    sold: List[str]

app = FastAPI()

@app.get("/")
def root():
    return {"Welcome to": "your first API in FastAPI!"}