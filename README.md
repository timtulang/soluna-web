Markdown

# Soluna: Lexical Analyzer

Soluna is a full-stack web application for lexical analysis, featuring a real-time symbol table and error reporting. It consists of a Python **FastAPI** backend and a **React/Vite** frontend.

## 📂 Project Structure

Ensure your project directory matches this structure before running:

```text
/soluna-root
  ├── backend/              # FastAPI Backend
  │     ├── app/
  │     │    └── main.py    # Main entry point (app.main:app)
  │     ├── .venv/          # Virtual Environment (auto-created)
  │     └── requirements.txt
  ├── soluna-ui/            # React Frontend
  │     ├── src/
  │     ├── package.json
  │     └── ...
  ├── soluna.py             # Automation Script
  └── README.md
```
### 🚀 Quick Start (Recommended)

We have included a cross-platform automation script (soluna.py) that handles setup, installation, and execution automatically.

#### Prerequisites

    Python 3.x installed and added to PATH.

    Node.js & npm installed and added to PATH.

#### How to Run
- Open your terminal/command prompt in the project root.

- Run the automation script:
    ```bash
    python soluna.py
    ```
    
- (On some Linux/Mac systems, you may need to use python3 soluna.py)

#### What this script does:

    ✅ Detects your OS (Windows/Linux/Mac).

    ✅ Checks for Python and Node.js prerequisites.

    ✅ Automatically creates a Python Virtual Environment (.venv or venv).

    ✅ Installs backend dependencies from requirements.txt.

    ✅ Installs frontend dependencies (node_modules) if missing.

    ✅ Launches both the Backend (Port 8000) and Frontend simultaneously.

### 🛠 Manual Setup

If you prefer to run the services manually or encounter issues with the script, follow these steps:

#### 1. Backend Setup

Navigate to the backend directory:
```bash
cd backend
```
Create a Virtual Environment:

    Windows: python -m venv .venv

    Mac/Linux: python3 -m venv .venv

Activate the Environment:

    Windows: .venv\Scripts\activate

    Mac/Linux: source .venv/bin/activate

Install Dependencies:
```bash
pip install -r requirements.txt
```
Run the Server:
```bash
# Note: Ensure you run this from the 'backend' directory
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
#### 2. Frontend Setup

Open a new terminal and navigate to the UI directory:
```bash
cd soluna-ui
```
Install Dependencies:
```bash
npm install
```
Run the Development Server:
```bash
npm run dev
```
#### 🔧 Troubleshooting

"Error: The python executable was not found..." If the automation script fails saying the virtual environment is broken, simply delete the backend/.venv (or backend/venv) folder. The script contains a self-healing feature and will recreate it correctly on the next run.

#### Port Conflicts
- The Backend runs on http://localhost:8000.

- The Frontend usually runs on http://localhost:5173 (Vite default).

- Ensure these ports are not being used by other applications.