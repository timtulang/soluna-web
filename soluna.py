import os
import sys
import subprocess
import platform
import threading
import time
import shutil

# --- CONFIGURATION ---
# Absolute paths to prevent directory confusion
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
FRONTEND_DIR = os.path.join(BASE_DIR, "soluna-ui")
BACKEND_HOST = "0.0.0.0"
BACKEND_PORT = "8000"

# Detect OS
IS_WINDOWS = platform.system() == "Windows"

# Define commands based on OS
PYTHON_EXEC = "python" if IS_WINDOWS else "python3"
NPM_EXEC = "npm.cmd" if IS_WINDOWS else "npm"

# Virtual Environment Paths (Absolute)
VENV_DIR = os.path.join(BACKEND_DIR, ".venv")
if IS_WINDOWS:
    VENV_PYTHON = os.path.join(VENV_DIR, "Scripts", "python.exe")
else:
    VENV_PYTHON = os.path.join(VENV_DIR, "bin", "python")

def print_colored(text, color="cyan"):
    """Simple helper to print colored text."""
    colors = {
        "cyan": "\033[96m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "reset": "\033[0m"
    }
    if IS_WINDOWS:
        print(f"--- {text} ---")
    else:
        print(f"{colors.get(color, '')}{text}{colors['reset']}")

def check_prerequisites():
    """Checks if Node and Python are actually installed globally."""
    print_colored("Checking Prerequisites...", "cyan")
    try:
        subprocess.run([PYTHON_EXEC, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("Python found.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_colored("Error: Python is not installed or not in PATH.", "red")
        sys.exit(1)

    try:
        subprocess.run(["npm", "-v"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=IS_WINDOWS, check=True)
        print("Node/NPM found.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_colored("Error: Node.js (npm) is not installed or not in PATH.", "red")
        sys.exit(1)

def setup_backend():
    """Sets up the Python Virtual Environment and installs requirements."""
    print_colored("Setting up Backend...", "cyan")

    # --- SELF-HEALING CHECK ---
    if os.path.exists(VENV_DIR) and not os.path.exists(VENV_PYTHON):
        print_colored("Detected broken virtual environment. Removing and recreating...", "yellow")
        try:
            shutil.rmtree(VENV_DIR)
        except Exception as e:
            print_colored(f"Error removing broken venv: {e}", "red")
            print("Please delete the 'backend/venv' folder manually.")
            sys.exit(1)

    # 1. Create Virtual Environment if it doesn't exist
    if not os.path.exists(VENV_DIR):
        print(f"Creating virtual environment in {VENV_DIR}...")
        try:
            subprocess.run([PYTHON_EXEC, "-m", "venv", VENV_DIR], check=True)
        except subprocess.CalledProcessError:
            print_colored("Error: Failed to create virtual environment.", "red")
            print("Possible Fixes:")
            print("1. If on Ubuntu/Debian: sudo apt install python3-venv")
            print("2. If on Arch: sudo pacman -S python")
            sys.exit(1)
    else:
        print("Virtual environment found and looks valid. Skipping creation.")

    # 2. Install Dependencies
    req_file = "requirements.txt" 
    abs_req_path = os.path.join(BACKEND_DIR, req_file)
    
    if os.path.exists(abs_req_path):
        print("Installing/Verifying backend dependencies...")
        try:
            if not os.path.exists(VENV_PYTHON):
                 raise FileNotFoundError(f"Python binary missing at {VENV_PYTHON}")

            subprocess.run([VENV_PYTHON, "-m", "pip", "install", "-r", req_file], cwd=BACKEND_DIR, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
             print_colored(f"Error during pip install: {e}", "red")
             sys.exit(1)
    else:
        print_colored(f"Warning: {abs_req_path} not found. Skipping pip install.", "yellow")

def setup_frontend():
    """Installs Node modules."""
    print_colored("Setting up Frontend...", "cyan")
    
    node_modules_path = os.path.join(FRONTEND_DIR, "node_modules")
    
    if os.path.exists(node_modules_path):
        print("node_modules found. Skipping 'npm install'.")
    else:
        print("Installing frontend dependencies (this may take a moment)...")
        subprocess.run([NPM_EXEC, "install"], cwd=FRONTEND_DIR, shell=IS_WINDOWS, check=True)

def run_backend_process():
    """Runs the FastAPI server using the venv python."""
    print_colored("Starting Backend Server...", "green")
    
    # --- FIXED COMMAND ---
    # Changed "main:app" to "app.main:app" to match your manual command
    cmd = [
        VENV_PYTHON, "-m", "uvicorn", 
        "app.main:app",  # <--- UPDATED HERE
        "--host", BACKEND_HOST, 
        "--port", BACKEND_PORT, 
        "--reload"
    ]
    
    try:
        # We keep cwd=BACKEND_DIR so it finds the 'app' folder inside 'backend'
        subprocess.run(cmd, cwd=BACKEND_DIR)
    except FileNotFoundError:
        print_colored(f"Error starting backend: Python binary not found at {VENV_PYTHON}", "red")

def run_frontend_process():
    """Runs the Vite development server."""
    print_colored("Starting Frontend Server...", "green")
    cmd = [NPM_EXEC, "run", "dev"]
    subprocess.run(cmd, cwd=FRONTEND_DIR, shell=IS_WINDOWS)

def main():
    print_colored(f"Detected OS: {platform.system()}", "yellow")
    
    check_prerequisites()
    
    try:
        setup_backend()
        setup_frontend()
    except Exception as e:
        print_colored(f"Setup failed: {e}", "red")
        return

    print_colored("Setup Complete! Launching services...", "green")
    time.sleep(1)

    backend_thread = threading.Thread(target=run_backend_process)
    frontend_thread = threading.Thread(target=run_frontend_process)

    backend_thread.daemon = True
    frontend_thread.daemon = True

    backend_thread.start()
    frontend_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print_colored("\nStopping services...", "red")
        sys.exit(0)

if __name__ == "__main__":
    main()