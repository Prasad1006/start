# backend/main.py

from fastapi import FastAPI
# ** THIS IS THE CRITICAL FIX **
# The '.' tells Python to look for the 'src' directory relative to this file's location.
from .src.users import router as users_router
# from .src.learning import router as learning_router # This will be added in a future phase

app = FastAPI(
    title="Learn N Teach API",
    description="The backend for the peer-to-peer learning platform.",
    version="1.0.0"
)

# Include the routers from each module to make their endpoints available.
app.include_router(users_router)
# app.include_router(learning_router)

@app.get("/api", include_in_schema=False)
def read_root():
    """A simple health-check endpoint."""
    return {"message": "Welcome to the Learn N Teach API!"}