from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from main import load_or_create_faceset, register_user
from typing import Dict
import uvicorn

app = FastAPI(title="Face Recognition API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize faceset data at startup
faceset_data = load_or_create_faceset()

@app.post("/register/")
async def register_face(file: UploadFile = File(...)) -> Dict[str, str]:
    try:
        # Create temp directory if it doesn't exist
        os.makedirs("temp", exist_ok=True)
        
        # Save uploaded file temporarily
        temp_path = os.path.join("temp", file.filename)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process registration
        result = register_user(temp_path, faceset_data)
        
        # Clean up
        os.remove(temp_path)
        
        return {"message": result}
        
    except Exception as e:
        return {"message": f"Error: {str(e)}"}
    
if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)