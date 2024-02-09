from sqlalchemy import  Column, Integer, String, Text, DateTime, Boolean, ForeignKey,LargeBinary
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
from sqlalchemy.sql import func






class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    # profile_image = Column(String)  
    email = Column(String, unique=True, nullable=False)
    firstname = Column(String)
    lastname = Column(String)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    
    projects = relationship('Project', back_populates='user')
    images = relationship('ImageModel', back_populates='user')


class OTPRecord(Base):
    __tablename__ = 'otp_records'

    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False)
    otp = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    # profile_image = Column(String) 
    brief_description = Column(Text)
    detailed_description = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default='pending')
    
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='projects')
    
    todos = relationship('Todo', back_populates='project')


class Todo(Base):
    __tablename__ = 'todos'
    
    id = Column(Integer, primary_key=True)
    task_title = Column(String, nullable=False)
    task_description = Column(Text)
    completed = Column(Boolean, default=False)
    
    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship('Project', back_populates='todos')
    
    resources = relationship('Resource', back_populates='todo')


class Resource(Base):
    __tablename__ = 'resources'
    
    id = Column(Integer, primary_key=True)
    resource_title = Column(String, nullable=False)
    resource_description = Column(Text)
    link = Column(String)
    resource_type = Column(String)
    
    todo_id = Column(Integer, ForeignKey('todos.id'))
    todo = relationship('Todo', back_populates='resources')









class ImageModel(Base):
    __tablename__ = 'images'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    mimetype = Column(String)
    image_data = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # New fields for the relationship with User
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='images')
