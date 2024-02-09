from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class UserRequest(BaseModel):
    email: EmailStr
    firstname: str = Field(min_length=3)
    lastname: str = Field(min_length=3)
    username: str = Field(min_length=5)
    password: str
    is_active: bool = Field(default=False)
    # profile_image: Optional[str]

class UserResponse(BaseModel):
    id: int
    firstname:str
    lastname: str
    username:str
    email:str


class UsersVerification(BaseModel):
    password: str
    new_password: str = Field(min_length=8)


class ProjectRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)  
    brief_description: str = Field(..., max_length=225)
    detailed_description: Optional[str] = None
    status: str | None = "un_completed"


class ProjectResponse(ProjectRequest):
    id:int
    user_id: int


    class Config:
        Attributes = True
        

class TodoRequest(BaseModel):
    task_title: str = Field(..., min_length=3 , max_length= 50)
    task_description: Optional[str] = Field(max_length=104)
    completed:bool = Field(default=False)


class TodoResponse(TodoRequest):
    id: int
    task_title: str
    task_description: str
    project_id: int
    completed: bool


class ResourceRequest(BaseModel):
    resource_title: str = Field(...,min_length=3, max_length=30)
    resource_description: str = Field(min_length=10, max_length=100)
    link:str = Field(...)
    resource_type:str = "web page"


class ResourceResponse(ResourceRequest):
    id: int
    resource_title: str
    resource_description: str
    link: str
    resource_type:str
    todo_id: int


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class OtpSchema(BaseModel):
    code: int
    
class ImageSchema(BaseModel):
    id: Optional[int] = Field(None, example=1)
    name: str = Field(..., example='example.png')
    mimetype: Optional[str] = Field(None, example='image/png')
    created_at: Optional[datetime] = None

    class Config:
        atribute = True


