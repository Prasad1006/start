# main.py
# This is the heart of our backend.

from fastapi import FastAPI

# Create an instance of the FastAPI class
# This 'app' object will be our main point of interaction
app = FastAPI()

# Define a "route" or "endpoint"
# The @app.get("/api/health") is a "decorator".
# It tells FastAPI that the function right below it is in charge of
# handling GET requests that come to the URL "/api/health".
@app.get("/api/health")
def read_root():
    # This function will be executed when a user visits http://your-website.com/api/health
    # It returns a Python dictionary. FastAPI automatically converts this
    # dictionary into JSON format, which is the standard language of APIs.
    return {"status": "ok", "message": "Backend is healthy!"}