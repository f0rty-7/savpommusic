from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles

from .database import engine, init_db
from .routers.music import router as music_router

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static" / "music"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

init_db()

app = FastAPI(
    title="Sava&Pomom Music Backend",
    description="API для стримингового музыкального сервиса Sava&Pomom Music",
    version="0.1.0",
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    def fix_upload_schema(schema):
        if isinstance(schema, dict):
            if schema.get("type") == "array":
                items = schema.get("items")
                if isinstance(items, dict) and items.get("type") == "string" and "contentMediaType" in items:
                    items["format"] = "binary"
                    items.pop("contentMediaType", None)
            for value in schema.values():
                fix_upload_schema(value)
        elif isinstance(schema, list):
            for item in schema:
                fix_upload_schema(item)

    fix_upload_schema(openapi_schema.get("components", {}))
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(music_router, prefix="/api")


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Sava&Pomom Music backend работает"}
