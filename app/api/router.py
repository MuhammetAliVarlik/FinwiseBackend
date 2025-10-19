from fastapi import APIRouter
from controllers.user_controller import UserController
from controllers.stock_controller import StockController

api_router = APIRouter()

user_controller = UserController()
stock_controller = StockController()

api_router.include_router(user_controller.register_routes())
api_router.include_router(stock_controller.register_routes())
