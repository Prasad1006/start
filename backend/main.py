from fastapi import FastAPI
# ** THIS IS THE FIX **
# Instead of importing the whole module, we import the specific 'router'
# variable from within the module.
from backend.src.users.router import router as users_router
from backend.src.learning.router import router as learning_router

app = FastAPI(title="Learn N Teach API")

# Now, 'users_router' is the actual APIRouter object that FastAPI expects.
app.include_router(users_router)
app.include_router(learning_router)

@app.get("/api", include_in_schema=False)
def read_root():
    """A simple health-check endpoint."""
    return {"message": "Welcome to the Learn N Teach API!"}