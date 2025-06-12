# backend/main.py

from fastapi import FastAPI
# ** THIS IS THE FIX **
# We use 'src.users' to tell Python to look inside the 'src' folder
# for the 'users' module.
from src.users import router as users_router
from src.learning import router as learning_router
# from src.sessions import router as sessions_router # Will be added in a future phase

app = FastAPI(
    title="Learn N Teach API",
    description="The backend for the peer-to-peer learning platform.",
    version="1.0.0"
)

# Include the routers from each module
app.include_router(users_router)
app.include_router(learning_router)
# app.include_router(sessions_router)

@app.get("/api")
def read_root():
    return {"message": "Welcome to the Learn N Teach API!"}