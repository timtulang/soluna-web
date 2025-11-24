import os
import sys
import subprocess
import platform
import threading
import time

# --- CONFIGURATION ---
BACKEND_DIR = "backend"
FRONTEND_DIR = "frontend"
BACKEND_HOST = "0.0.0.0"
BACKEND_PORT = "8000"

# Detect OS
IS_WINDOWS = platform.system() == "Windows"

# Define commands based on OS
PYTHON_EXEC = "python" if IS_WINDOWS else "python3"
PIP_EXEC = "pip" if IS_WINDOWS else "pip3"
NPM_EXEC = "npm.cmd" if IS_WINDOWS else "npm"

# Virtual Environment Paths
VENV_DIR = os.path.join(BACKEND_DIR, "venv")
if IS_WINDOWS:
    VENV_PYTHON = os.path.join(VENV_DIR, "Scripts", "python.exe")
    VENV_PIP = os.path.join(VENV_DIR, "Scripts", "pip.exe")
else:
    VENV_PYTHON = os.path.join(VENV_DIR, "bin", "python")
    VENV_PIP = os.path.join(VENV_DIR, "bin", "pip")

def print_colored(text, color="cyan"):
    """Simple helper to print colored text for better visibility."""
    colors = {
        "cyan": "\033[96m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "reset": "\033[0m"
    }
    # ANSI codes don't always work in standard Windows CMD, so we skip if needed
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
    
    # 1. Create Virtual Environment if it doesn't exist
    if not os.path.exists(VENV_DIR):
        print(f"Creating virtual environment in {VENV_DIR}...")
        subprocess.run([PYTHON_EXEC, "-m", "venv", VENV_DIR], check=True)
    else:
        print("Virtual environment found. Skipping creation.")

    # 2. Install Dependencies
    # We check if the venv has packages installed by running a simple pip freeze
    # This is a basic check; pip install is fast if requirements are already satisfied
    req_file = os.path.join(BACKEND_DIR, "requirements.txt")
    if os.path.exists(req_file):
        print("Installing/Verifying backend dependencies...")
        subprocess.run([VENV_PIP, "install", "-r", "requirements.txt"], cwd=BACKEND_DIR, check=True)
    else:
        print_colored(f"Warning: {req_file} not found. Skipping pip install.", "yellow")

def setup_frontend():
    """Installs Node modules."""
    print_colored("Setting up Frontend...", "cyan")
    
    node_modules_path = os.path.join(FRONTEND_DIR, "node_modules")
    
    # 1. Check if node_modules exists
    if os.path.exists(node_modules_path):
        print("node_modules found. Skipping 'npm install'.")
    else:
        print("Installing frontend dependencies (this may take a moment)...")
        subprocess.run([NPM_EXEC, "install"], cwd=FRONTEND_DIR, shell=IS_WINDOWS, check=True)

def run_backend_process():
    """Runs the FastAPI server using the venv python."""
    print_colored("Starting Backend Server...", "green")
    # Using uvicorn directly via python -m to ensure we use the venv
    cmd = [VENV_PYTHON, "-m", "uvicorn", "main:app", "--host", BACKEND_HOST, "--port", BACKEND_PORT, "--reload"]
    subprocess.run(cmd, cwd=BACKEND_DIR)

def run_frontend_process():
    """Runs the Vite development server."""
    print_colored("Starting Frontend Server...", "green")
    cmd = [NPM_EXEC, "run", "dev"]
    subprocess.run(cmd, cwd=FRONTEND_DIR, shell=IS_WINDOWS)

def main():
    print_colored(f"Detected OS: {platform.system()}", "yellow")
    
    check_prerequisites()
    
    # --- INSTALLATION PHASE ---
    try:
        setup_backend()
        setup_frontend()
    except Exception as e:
        print_colored(f"Setup failed: {e}", "red")
        return

    print_colored("Setup Complete! Launching services...", "green")
    time.sleep(1)

    # --- EXECUTION PHASE ---
    # We use threading to run both blocking processes at the same time
    backend_thread = threading.Thread(target=run_backend_process)
    frontend_thread = threading.Thread(target=run_frontend_process)

    # Daemon threads exit when the main program exits (Ctrl+C)
    backend_thread.daemon = True
    frontend_thread.daemon = True

    backend_thread.start()
    frontend_thread.start()

    try:
        # Keep the main script alive to listen for Ctrl+C
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print_colored("\nStopping services...", "red")
        sys.exit(0)

if __name__ == "__main__":
    main()