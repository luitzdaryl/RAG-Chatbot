from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
import json

from rag import ask_ai_stream, retrieve

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def root():
    return {"message": "RAG API is running"}

@app.post("/chat")
def chat(request: ChatRequest):
    sources = retrieve(request.message)

    def generate():
        # First, send sources as the first chunk
        yield json.dumps({"type": "sources", "data": sources}) + "\n"

        # Then stream the AI tokens
        for chunk in ask_ai_stream(request.message, sources):
            yield json.dumps({"type": "token", "data": chunk}) + "\n"

    return StreamingResponse(generate(), media_type="text/plain")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)