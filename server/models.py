from typing import List
from pydantic import BaseModel
class ProjectBase(BaseModel):
    project_id : str
    project_title: str


class UserBase(BaseModel):
    user_name: str
    projects : List[ProjectBase]
