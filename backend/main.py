from fastapi import FastAPI
# We will import the modules directly, and they will handle their own sub-imports.
from backend.src.users import router as users_router
from backend.src.learning import router as learning_router

app = FastAPI(title="Learn N Teach API")

# Include the routers from each module
app.include_router(users_router)
app.include_router(learning_router)

@app.get("/api", include_in_schema=False)
def read_root():
    return {"message": "Welcome to the Learn N Teach API!"}