import time
import uuid
import contextvars
import traceback
from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List
from logger import logger

app = FastAPI()

# Context variable to hold correlation ID across async calls
correlation_id_var = contextvars.ContextVar("correlation_id", default="unknown")

# --- Middlewares ---

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    # 1. Extract or generate Correlation ID
    corr_id = request.headers.get("x-correlation-id", f"req_{uuid.uuid4().hex[:8]}")
    correlation_id_var.set(corr_id)
    
    start_time = time.time()
    
    try:
        # Process the request
        response = await call_next(request)
        
        # Log request completed (Mimicking pinoHttp customSuccessMessage)
        logger.info(
            "request_completed",
            extra={
                "tags": {"correlationId": corr_id},
                "req": {"method": request.method, "url": str(request.url)},
                "res": {"status_code": response.status_code},
                "responseTime_ms": round((time.time() - start_time) * 1000, 2)
            }
        )
        return response
        
    except Exception as e:
        # Log request error (Mimicking pinoHttp customErrorMessage)
        logger.error(
            f"request_error: {str(e)}",
            extra={
                "tags": {"correlationId": corr_id},
                "req": {"method": request.method, "url": str(request.url)},
                "err": traceback.format_exc()
            }
        )
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )

# --- Helper to append context to manual logs ---
def log_with_context(level: str, msg: str, extra_data: dict = None):
    extra = {"tags": {"correlationId": correlation_id_var.get()}}
    if extra_data:
        extra.update(extra_data)
    getattr(logger, level)(msg, extra=extra)

# --- Data Models (Automatic Validation!) ---
class OrderCreate(BaseModel):
    customer: str
    items: List[str] = Field(min_length=1)

class OrderUpdate(BaseModel):
    status: str

# --- In-memory DB ---
orders = {}

# --- Routes ---

@app.post("/orders", status_code=status.HTTP_201_CREATED)
def create_order(order: OrderCreate):
    # If the payload is invalid, FastAPI automatically returns 422 (like your 400 bad request)
    order_id = f"ord_{int(time.time() * 1000)}"
    
    new_order = {
        "id": order_id,
        "customer": order.customer,
        "items": order.items,
        "status": "CREATED",
        "createdAt": datetime.now(timezone.utc).isoformat() + "Z"
    }
    orders[order_id] = new_order
    
    log_with_context("info", "order_created", {"orderId": order_id})
    return new_order

@app.get("/orders/{order_id}")
def get_order(order_id: str):
    order = orders.get(order_id)
    if not order:
        log_with_context("warning", "order_not_found", {"orderId": order_id})
        raise HTTPException(status_code=404, detail="Order not found")
        
    log_with_context("info", "order_fetched", {"orderId": order_id})
    return order

@app.patch("/orders/{order_id}")
def update_order(order_id: str, order_update: OrderUpdate):
    order = orders.get(order_id)
    if not order:
        log_with_context("warning", "order_not_found", {"orderId": order_id})
        raise HTTPException(status_code=404, detail="Order not found")
        
    order["status"] = order_update.status
    log_with_context("info", "order_updated", {"orderId": order_id, "newStatus": order_update.status})
    return order

@app.get("/simulate-error")
def simulate_error():
    try:
        raise ValueError("Simulated internal failure")
    except Exception as err:
        log_with_context("error", "internal_error", {"stack": traceback.format_exc()})
        raise HTTPException(status_code=500, detail="Internal error")

@app.get("/")
def read_root():
    return "Order Service is running as expected."

# FastAPI standard is to run via `fastapi dev main.py` or `uvicorn main:app`, 
# but if you run this file directly (like `node server.js`), this block executes:
if __name__ == "__main__":
    import uvicorn
    logger.info("Order service starting...")
    uvicorn.run("main:app", host="0.0.0.0", port=3000)