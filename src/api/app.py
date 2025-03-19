import logging
import time
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from mangum import Mangum
import uvicorn

from api.routers import model, chat, embeddings
from api.setting import API_ROUTE_PREFIX, TITLE, DESCRIPTION, SUMMARY, VERSION
from starlette.middleware.base import BaseHTTPMiddleware

# Configure Logging to DEBUG
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO to DEBUG
    format="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s",
)

# FastAPI Configuration
config = {
    "title": TITLE,
    "description": DESCRIPTION,
    "summary": SUMMARY,
    "version": VERSION,
}

app = FastAPI(**config)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging Middleware for Request/Response Logging
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Log the request details
        logging.debug(
            f"{request.method} {request.url} - Status: {response.status_code} - Time: {process_time:.4f}s"
        )
        logging.debug(
            f" Status: {response.status_code} - Time: {process_time}"
        )
        logging.flush()

        return response

# Add Logging Middleware
app.add_middleware(LoggingMiddleware)

# Include API Routers
app.include_router(model.router, prefix=API_ROUTE_PREFIX)
app.include_router(chat.router, prefix=API_ROUTE_PREFIX)
app.include_router(embeddings.router, prefix=API_ROUTE_PREFIX)

# Health Check Endpoint
@app.get("/health")
async def health():
    """For health check if needed"""
    return {"status": "OK"}

# Exception Handler for Validation Errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logging.error("Validation Error: app:" + str(exc))
    logging.flush()
    return PlainTextResponse(str(exc), status_code=400)

# AWS Lambda Handler
handler = Mangum(app)

# Run Uvicorn with Debug Logs Enabled
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug",  # Enabled debug logs for Uvicorn
    )
