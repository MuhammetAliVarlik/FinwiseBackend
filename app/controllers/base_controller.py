# app/controllers/base_controller.py
from fastapi import APIRouter
from typing import List

class BaseController:
    def __init__(self, prefix: str = "", tags: List[str] = None):
        self.router = APIRouter(prefix=prefix, tags=tags or [])
