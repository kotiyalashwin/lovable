from sqlalchemy import Boolean,Column, ForeignKey,Integer, String
from sqlalchemy.orm import relationship
from .db import Base



class Users(Base):
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True,nullable=False)

    projects = relationship("Project", back_populates="owner", cascade="all,delete-orphan")

class Projects(Base):
    __tablename__ = 'projects'

    project_id = Column(String,primary_key=True,index=True)
    projecct_title = Column(String)
