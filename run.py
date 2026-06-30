import os
import sys
import time
import subprocess
import signal

# Track processes globally to kill them on exit
processes = []


def signal_handler(sig, frame):
    print("\nShutting down WiFi RRM Prototype servers...")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def main():
    print("==========================================================")
    print("Starting AI-Assisted WiFi Radio Resource Management System")
    print("==========================================================")

    project_root = os.path.dirname(os.path.abspath(__file__))

    # -------------------------------------------------------
    # Locate Python executable
    # -------------------------------------------------------
    venv_dir = os.path.join(project_root, "venv")
    if not os.path.exists(venv_dir):
        venv_dir = os.path.join(project_root, ".venv")

    if os.path.exists(venv_dir):
        if sys.platform == "win32":
            python_bin = os.path.join(venv_dir, "Scripts", "python.exe")
        else:
            python_bin = os.path.join(venv_dir, "bin", "python")
    else:
        print("Virtual environment not detected. Using system Python.")
        python_bin = sys.executable

    print(f"Using Python: {python_bin}")
    print("Launching Streamlit via: python -m streamlit")

    os.chdir(project_root)

    env = os.environ.copy()
    env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")

    # -------------------------------------------------------
    # Start FastAPI
    # -------------------------------------------------------
    print("\n1. Bootstrapping FastAPI backend server on port 8000...")

    backend_cmd = [
        python_bin,
        "-m",
        "uvicorn",
        "src.api.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ]

    try:
        backend_proc = subprocess.Popen(
            backend_cmd,
            env=env,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        processes.append(backend_proc)
    except Exception as e:
        print(f"Failed to start backend: {e}")
        sys.exit(1)

    print("Waiting 4 seconds for API startup...")
    time.sleep(4)

    # -------------------------------------------------------
    # Start Streamlit
    # -------------------------------------------------------
    print("\n2. Bootstrapping Streamlit Dashboard on port 8501...")

    dashboard_path = os.path.join("dashboard", "app.py")

    streamlit_cmd = [
        python_bin,
        "-m",
        "streamlit",
        "run",
        dashboard_path,
        "--server.port",
        "8501",
        "--server.address",
        "127.0.0.1",
    ]

    try:
        dashboard_proc = subprocess.Popen(
            streamlit_cmd,
            env=env,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        processes.append(dashboard_proc)
    except Exception as e:
        print(f"Failed to start dashboard: {e}")
        backend_proc.terminate()
        sys.exit(1)

    print("\n==========================================================")
    print("FastAPI Backend Docs : http://127.0.0.1:8000/docs")
    print("Streamlit Dashboard : http://127.0.0.1:8501")
    print("Press Ctrl+C to stop both servers.")
    print("==========================================================")

    while True:
        backend_exit = backend_proc.poll()
        dashboard_exit = dashboard_proc.poll()

        if backend_exit is not None:
            print(f"\nBackend exited with code {backend_exit}")
            dashboard_proc.terminate()
            break

        if dashboard_exit is not None:
            print(f"\nDashboard exited with code {dashboard_exit}")
            backend_proc.terminate()
            break

        time.sleep(1)


if __name__ == "__main__":
    main()