import os
import sys
import time
import subprocess
import signal
import sys

# Track processes globally to kill them on exit
processes = []

def signal_handler(sig, frame):
    print("\nShutting down WiFi RRM Prototype servers...")
    for proc in processes:
        try:
            # Send SIGTERM to subprocesses
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    sys.exit(0)

# Register signal handler for Ctrl+C
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    print("==========================================================")
    print("Starting AI-Assisted WiFi Radio Resource Management System")
    print("==========================================================")
    
    # Path to virtual environment python executable or system python
    venv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv")
    if not os.path.exists(venv_dir):
        # Fallback to secondary name ".venv" if it exists
        venv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv")
        
    if os.path.exists(venv_dir):
        if sys.platform == "win32":
            python_bin = os.path.join(venv_dir, "Scripts", "python.exe")
            streamlit_bin = os.path.join(venv_dir, "Scripts", "streamlit.exe")
        else:
            python_bin = os.path.join(venv_dir, "bin", "python")
            streamlit_bin = os.path.join(venv_dir, "bin", "streamlit")
    else:
        print("Virtual environment not detected. Using default system paths...")
        python_bin = sys.executable
        # Find streamlit in system PATH
        streamlit_bin = "streamlit"

    # Verify python path
    print(f"Using Python: {python_bin}")
    print(f"Using Streamlit: {streamlit_bin}")

    # Set working directory to project root
    cwd = os.path.dirname(os.path.abspath(__file__))
    os.chdir(cwd)

    # 1. Start FastAPI Backend Process
    print("\n1. Bootstrapping FastAPI backend server on port 8000...")
    backend_cmd = [python_bin, "-m", "uvicorn", "src.api.main:app", "--host", "127.0.0.1", "--port", "8000"]
    
    # Run with system path injection for imports
    env = os.environ.copy()
    env["PYTHONPATH"] = cwd + os.pathsep + env.get("PYTHONPATH", "")

    try:
        backend_proc = subprocess.Popen(
            backend_cmd,
            env=env,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        processes.append(backend_proc)
    except Exception as e:
        print(f"Error starting FastAPI backend: {e}")
        sys.exit(1)

    # Allow the database schema migration and background seed to complete
    print("Waiting 4 seconds for API startup and database initialization...")
    time.sleep(4)

    # 2. Start Streamlit Dashboard Process
    print("\n2. Bootstrapping Streamlit Dashboard on port 8501...")
    dashboard_path = os.path.join("dashboard", "app.py")
    streamlit_cmd = [streamlit_bin, "run", dashboard_path, "--server.port", "8501", "--server.address", "127.0.0.1"]

    try:
        dashboard_proc = subprocess.Popen(
            streamlit_cmd,
            env=env,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        processes.append(dashboard_proc)
    except Exception as e:
        print(f"Error starting Streamlit Dashboard: {e}")
        # Terminate backend since dashboard failed
        backend_proc.terminate()
        sys.exit(1)

    print("\n==========================================================")
    print("FastAPI Backend Docs:   http://127.0.0.1:8000/docs")
    print("Streamlit Dashboard:    http://127.0.0.1:8501")
    print("Press Ctrl+C to terminate both servers.")
    print("==========================================================")

    # Maintain runner loop to monitor process status
    while True:
        # Check if either process terminated
        backend_exit = backend_proc.poll()
        dashboard_exit = dashboard_proc.poll()

        if backend_exit is not None:
            print(f"\nBackend process exited with code {backend_exit}. Shutting down dashboard...")
            dashboard_proc.terminate()
            break
        
        if dashboard_exit is not None:
            print(f"\nDashboard process exited with code {dashboard_exit}. Shutting down backend...")
            backend_proc.terminate()
            break

        time.sleep(1)

if __name__ == "__main__":
    main()
