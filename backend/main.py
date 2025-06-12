from fastapi import FastAPI
# The imports are now clean and direct because the folders are siblings to this file.
from users import router as users_router
from learning import router as learning_router

app = FastAPI(title="Learn N Teach API")

app.include_router(users_router)
app.include_router(learning_router)

@app.get("/api", include_in_schema=False)
def read_root():
    return {"message": "Welcome to the Learn N Teach API!"}