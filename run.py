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


def start_api(port="8000"):
    """Start FastAPI server."""
    print(f"Starting FastAPI backend on http://localhost:{port}")
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "0.0.0.0", "--port", str(port)],
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
    print("  NagrikMitra - Unified Citizen Interaction Assistant")
    print("  Powered by Sarvam AI Cloud")
    print("=" * 60)
    print()

    check_env()

    args = sys.argv[1:]
    processes = []
    
    port = os.environ.get("PORT", "8000")
    is_railway = "RAILWAY_ENVIRONMENT_NAME" in os.environ or "RAILWAY_PROJECT_ID" in os.environ or os.environ.get("PORT")

    if "--api" in args or is_railway:
        processes.append(start_api(port=port))
        if is_railway:
            print("Detected Railway Environment. Running ONLY the FastAPI backend.")
    elif "--ui" in args:
        processes.append(start_ui())
    else:
        # Start both locally
        api_proc = start_api(port=port)
        processes.append(api_proc)
        time.sleep(2)  # Let API start before UI
        ui_proc = start_ui()
        processes.append(ui_proc)

        print()
        print("✅ Both servers running:")
        print(f"   API:  http://localhost:{port}/docs")
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
