import uuid
from sqlalchemy import UUID, Column, String
from sqlalchemy.orm import relationship
from .db import Base



class User(Base):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True,default=uuid.uuid4)
    email = Column(String, unique=True,nullable=False)
    #user.projects
    projects = relationship("Project", back_populates="owner", cascade="all,delete-orphan")

class Project(Base):
    __tablename__ = 'projects'

    project_id = Column(String,primary_key=True,index=True)
    project_title = Column(String)
    #project.owner
    owner_id = Column(String, ForeignKey="users.id",nullable=False)
    owner = relationship("User",back_populates='projects')
