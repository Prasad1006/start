from fastapi import FastAPI
# The imports are now clean and direct because the folders are siblings to this file.
from users import router as users_router

# We comment out the learning router because its file doesn't exist yet.
# from learning import router as learning_router

app = FastAPI(
    title="Learn N Teach API",
    description="The backend for the peer-to-peer learning platform.",
    version="1.0.0"
)

# We only include the router for the module that is complete.
app.include_router(users_router)
# app.include_router(learning_router)

@app.get("/api", include_in_schema=False)
def read_root():
    """A simple health-check endpoint."""
    return {"message": "Welcome to the Learn N Teach API!"}