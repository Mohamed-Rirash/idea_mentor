from fastapi import FastAPI
from . import models
from app.database import engine
from app.routers import auth,projects,todos,users,resources,profile,google_auth
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
import os

description = """
ideamentor API is used to manage your ideas and  do awesome stuff. 🚀

## projects

You can **GRUD projects**.

## Users

You will be able to:

* **Create users and verify otp sent** .
* **login to created users** .
* **Read users info** 
* **change password** 
* **forget password** 

## Todos

You can **GRUD todo**. for specific project


## resources

You can **GRUD resources**. for specific task
.
"""

app = FastAPI(
    title="ideamentor",
    description=description,
    summary="this an app used to manage your project ideas.",
    version="0.0.1",
   
)
origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("AUTH_SECRET")
)

models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(google_auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(todos.router)
app.include_router(resources.router)
app.include_router(profile.router)


