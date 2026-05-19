Frontend: Vue.js
Backend API: FastAPI
LLM + embeddings: Ollama
Communication: HTTP requests

A clean beginner-friendly architecture:

Vue Frontend  --->  FastAPI Backend  --->  Ollama
                         |
                         ---> Vector DB / RAG Logic
## Step 1 — Project Structure

Create a folder structure like this:

rag-chatbot/
│
├── backend/
│   ├── main.py
│   ├── rag.py
│   ├── dataset/
│   │   └── cat-facts.txt
│   └── requirements.txt
│
└── frontend/

## Step 2 — Install Backend Dependencies

### Go into backend:

cd backend

### Create virtual environment:

python -m venv venv

### Activate it:

- Windows:
venv\Scripts\activate

- Mac/Linux
source venv/bin/activate

### Install packages:

pip install fastapi uvicorn ollama

### Save requirements:

pip freeze > requirements.txt


-------------------------------------
-------------------------------------

### Create Vue Frontend

Open another terminal.

Go back to root project:

cd ..

#### Create Vue app:

npm create vue@latest

#### Choose:

✔ Add Vue Router? Yes

#### Then:

cd frontend
npm install

#### Run frontend:

npm run dev

---------------------------------------------------------------
---------------------------------------------------------------

AI-MANAGER:

Admin:

Username: octon-aimanager
Password: ai-ml-dev-team@admin_#05182026

---------------------------------------------------

Username: aimanager-user
Password: 123456

---------------------------------------------------

