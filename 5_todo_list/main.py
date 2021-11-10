from datetime import timedelta
from fastapi import FastAPI, Request, Depends, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.encoders import jsonable_encoder
from db import SessionLocal, engine, DBContext
import models, crud, schemas
from sqlalchemy.orm import Session
from fastapi_login import LoginManager
from dotenv import load_dotenv
import os
from passlib.context import CryptContext
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
ACCESS_TOKEN_EXPIRE_MINUTES=60

manager = LoginManager(SECRET_KEY, token_url="/login", use_cookie=True)
manager.cookie_name = "auth"

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    with DBContext() as db:
        yield db

def get_hashed_password(plain_password):
    return pwd_ctx.hash(plain_password)

def verify_password(plain_password, hashed_password):
    return pwd_ctx.verify(plain_password,hashed_password)

@manager.user_loader()
def get_user(username: str, db: Session = None):
    if db is None:
        with DBContext() as db:
            return crud.get_user_by_username(db=db,username=username)
    return crud.get_user_by_username(db=db,username=username)

def authenticate_user(username: str, password: str, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db=db,username=username)
    if not user:
        return None
    if not verify_password(plain_password=password,hashed_password=user.hashed_password):
        return None
    return user

class NotAuthenticatedException(Exception):
    pass

def not_authenticated_exception_handler(request, exception):
    return RedirectResponse("/login")

manager.not_authenticated_exception = NotAuthenticatedException
app.add_exception_handler(NotAuthenticatedException, not_authenticated_exception_handler)

@app.get("/")
def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Home"})

@app.get("/tasks")
def get_tasks(db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    return jsonable_encoder(user)

@app.get("/login")
def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "title": "Login"})

@app.post("/login")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(username=form_data.username,password=form_data.password,db=db)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request,
        "title": "Login",
        "invalid": True}, status_code=status.HTTP_401_UNAUTHORIZED)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = manager.create_access_token(
        data={"sub": user.username},
        expires=access_token_expires
    )
    resp = RedirectResponse("/tasks", status_code=status.HTTP_302_FOUND)
    manager.set_cookie(resp,access_token)
    return resp