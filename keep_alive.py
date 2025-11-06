import os
from aiohttp import web

async def handle(request):
    """Simple handler that returns a 200 OK status."""
    return web.Response(text="I'm alive")

async def create_keep_alive_app():
    """Creates the aiohttp web application."""
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    return app
