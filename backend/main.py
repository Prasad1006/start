import sys
import os
from fastapi import FastAPI

# ** THIS IS THE CRITICAL FIX **
# Get the directory where this main.py file lives.
# On Vercel, this will be '/var/task/backend/'.
# We add the 'src' subdirectory to Python's path.
# Now, Python will know to look inside 'src/' for modules.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Now that the path is fixed, these imports will work perfectly.
from users import router as users_router
from learning import router as learning_router
# from sessions import router as sessions_router # For the future

app = FastAPI(
    title="Learn N Teach API",
    description="The backend for the peer-to-peer learning platform.",
    version="1.0.0"
)

# This part remains the same
app.include_router(users_router)
app.include_router(learning_router)
# app.include_router(sessions_router)

@app.get("/api", include_in_schema=False)
def read_root():
    """A simple health-check endpoint."""
    return {"message": "Welcome to the Learn N Teach API!"}