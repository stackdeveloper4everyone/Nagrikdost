"""NagrikMitra — One-command startup script.

Launches both FastAPI backend and Streamlit frontend.

Usage:
    python run.py           # Start both servers
    python run.py --api     # Start only FastAPI
    python run.py --ui      # Start only Streamlit
"""

import subprocess
import sys
import os
import time
import signal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def check_env():
    """Check if .env file exists and has API key."""
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_path):
        example_path = os.path.join(BASE_DIR, ".env.example")
        if os.path.exists(example_path):
            import shutil
            shutil.copy2(example_path, env_path)
            print("⚠️  Created .env from .env.example")
            print("   Please add your SARVAM_API_KEY to .env")
        else:
            print("⚠️  No .env file found. Create one with SARVAM_API_KEY=your_key")


def start_api():
    """Start FastAPI server."""
    print("🚀 Starting FastAPI backend on http://localhost:8000")
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=BASE_DIR,
    )


def start_ui():
    """Start Streamlit frontend."""
    print("🎨 Starting Streamlit frontend on http://localhost:8501")
    streamlit_app = os.path.join(BASE_DIR, "frontend", "streamlit_app.py")
    return subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", streamlit_app,
         "--server.port", "8501", "--server.address", "0.0.0.0",
         "--server.headless", "true",
         "--browser.gatherUsageStats", "false"],
        cwd=BASE_DIR,
    )


def main():
    print("=" * 60)
    print("  🏛️  NagrikMitra — Unified Citizen Interaction Assistant")
    print("  Powered by Sarvam AI Cloud")
    print("=" * 60)
    print()

    check_env()

    args = sys.argv[1:]
    processes = []

    if "--api" in args:
        processes.append(start_api())
    elif "--ui" in args:
        processes.append(start_ui())
    else:
        # Start both
        api_proc = start_api()
        processes.append(api_proc)
        time.sleep(2)  # Let API start before UI
        ui_proc = start_ui()
        processes.append(ui_proc)

        print()
        print("✅ Both servers running:")
        print("   API:  http://localhost:8000/docs")
        print("   UI:   http://localhost:8501")
        print()
        print("Press Ctrl+C to stop both servers")

    try:
        for proc in processes:
            proc.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        for proc in processes:
            proc.terminate()
        for proc in processes:
            proc.wait()
        print("👋 Goodbye!")


if __name__ == "__main__":
    main()
