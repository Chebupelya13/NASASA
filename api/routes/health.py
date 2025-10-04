from sanic import Blueprint
from sanic.response import json

bp = Blueprint("health_check", url_prefix="/")

@bp.get("/route1")
async def route1(request):
    """
    A placeholder for route 1.
    This can be used for a simple health check or other basic info.
    """
    return json({"message": "This is route 1"})

@bp.get("/route2")
async def route2(request):
    """
    A placeholder for route 2.
    """
    return json({"message": "This is route 2"})