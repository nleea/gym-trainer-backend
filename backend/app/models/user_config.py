from typing import Optional
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import JSON


class UserConfig(SQLModel, table=True):
    __tablename__ = "user_configs"

    id:      Optional[int] = Field(default=None, primary_key=True)
    user_id: str            = Field(index=True, unique=True)
    config:  dict           = Field(default_factory=dict, sa_column=Column(JSON, nullable=False, server_default="{}"))
