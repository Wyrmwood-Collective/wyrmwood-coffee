import logging
import shutil
import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import Scope

from wyrmwood_coffee.logging import setup_logging
from wyrmwood_coffee.middleware import RequestLoggingMiddleware
from wyrmwood_coffee.routers import (
    auth,
    baked_goods,
    customers,
    drinks,
    employees,
    ingredients,
    vendors,
)
from wyrmwood_coffee.routers.promotions import router as promotions_router

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(RequestLoggingMiddleware)
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(baked_goods.router, prefix="/baked-goods", tags=["Baked Goods"])
app.include_router(customers.router, prefix="/customers", tags=["Customers"])
app.include_router(drinks.router, prefix="/drinks", tags=["Drinks"])
app.include_router(employees.router)
app.include_router(ingredients.router)
app.include_router(promotions_router)
app.include_router(vendors.router, prefix="/vendors", tags=["Vendors"])


class SPAStaticFiles(StaticFiles):
    """Serves a built SPA, falling back to index.html for client-side routes."""

    async def get_response(self, path: str, scope: Scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code != 404:
                raise
            return await super().get_response("index.html", scope)


FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
FRONTEND_DIST_DIR = FRONTEND_DIR / "dist"
if FRONTEND_DIST_DIR.is_dir():
    app.mount(
        "/app",
        SPAStaticFiles(directory=FRONTEND_DIST_DIR, html=True),
        name="frontend",
    )


def dev():
    npm = shutil.which("npm")
    if npm is None:
        print("npm not found, install node to build frontend (see README)")
        sys.exit(1)
    subprocess.run([npm, "run", "build"], cwd=FRONTEND_DIR, check=True)
    subprocess.run(["fastapi", "dev", str(Path(__file__))])


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # log-level rationale (per WC-49 requirements):
    # error, because an unhandled exception indicates a failure path
    # we have not accounted for
    logger.error("Unhandled exception", exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/app/")


@app.get("/health")
def health():
    return {"message": "Welcome to Wyrmwood Coffee!"}
