from fastapi import Request
import aiohttp


async def get_session(request: Request) -> aiohttp.ClientSession:
    return request.app.state.session
