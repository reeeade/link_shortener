import json
import os
import random
import string
import motor.motor_asyncio
import aiofiles
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

app = FastAPI()
template = Jinja2Templates(directory="templates")
username = os.environ.get("MONGO_USERNAME", "root")
password = os.environ.get("MONGO_PASSWORD", "example")
hostname = os.environ.get("MONGO_HOST", "localhost")
port = os.environ.get("MONGO_PORT", "27017")
client = motor.motor_asyncio.AsyncIOMotorClient(f"mongodb://{username}:{password}@{hostname}:{port}/")


@app.get("/")
async def form_with_full_url(request: Request):
    return template.TemplateResponse("url_input.html", {"request": request})


async def save_json_to_file(short_url, long_url):
    if os.path.exists("urls.json"):
        async with aiofiles.open("urls.json", "r") as f:
            urls = json.loads(await f.read())
    else:
        urls = {}

    urls[short_url] = long_url

    async with aiofiles.open("urls.json", "w") as f:
        await f.write(json.dumps(urls, indent=4))


async def get_long_url(short_url: str):
    if os.path.exists("urls.json"):
        async with aiofiles.open("urls.json", "r") as f:
            urls = json.loads(await f.read())
        return urls.get(short_url)
    return None


@app.post("/")
async def record_url(long_url: str = Form()):
    # generate string with 4 random characters
    db = client["url_shortener"]
    collection = db["urls"]
    short_url = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(4))
    await collection.insert_one({"short_url": short_url, "long_url": long_url})
    return short_url


@app.get("/{short_url}")
async def redirect_to_long_url(short_url: str):
    db = client["url_shortener"]
    collection = db["urls"]
    # long_url = await get_long_url(short_url)
    doc_with_long_url = await collection.find_one({"short_url": short_url})
    if doc_with_long_url is not None:
        long_url = doc_with_long_url.get("long_url")
        if long_url:
            return RedirectResponse(url=long_url, status_code=302)
    else:
        return 'Not found'

