# backend/main.py
from fastapi import FastAPI
from users import router as users_router
from learning import router as learning_router
# from sessions import router as sessions_router # Will be added in a future phase

app = FastAPI(
    title="Learn N Teach API",
    description="The backend for the peer-to-peer learning platform.",
    version="1.0.0"
)

# Include the routers from each module
app.include_router(users_router.router)
app.include_router(learning_router.router)
# app.include_router(sessions_router.router)

@app.get("/api")
def read_root():
    return {"message": "Welcome to the Learn N Teach API!"}