import sys
from pathlib import Path
from fastapi import FastAPI

# ** THIS IS THE DEFINITIVE FIX **
# Add the 'backend' directory to Python's system path.
# This makes all subdirectories (like 'users', 'core') importable as top-level modules.
sys.path.append(str(Path(__file__).resolve().parent))

# Now, these simple imports will work correctly.
from users import router as users_router
# from learning import router as learning_router # We'll add this back when it's built

# --- App Initialization ---
app = FastAPI(title="Learn N Teach API")

app.include_router(users_router)
# app.include_router(learning_router)

@app.get("/api", include_in_schema=False)
def read_root():
    return {"message": "Welcome to the Learn N Teach API!"}