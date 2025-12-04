from contextlib import asynccontextmanager
import aiohttp
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.session = aiohttp.ClientSession()
    yield
    await app.state.session.close()
