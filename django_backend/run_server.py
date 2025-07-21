#!/usr/bin/env python3
"""
Script to run the Video Location Tracker FastAPI server
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install required packages"""
    print("Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        sys.exit(1)

def run_server():
    """Run the FastAPI server"""
    print("Starting Video Location Tracker API server...")
    print("Server will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error running server: {e}")

def main():
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🚀 Video Location Tracker API Server Setup")
    print("=" * 50)
    
    # Check if requirements.txt exists
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found!")
        sys.exit(1)
    
    # Check if main.py exists
    if not Path("main.py").exists():
        print("❌ main.py not found!")
        sys.exit(1)
    
    # Install requirements
    install_requirements()
    
    print("\n" + "=" * 50)
    
    # Run server
    run_server()

if __name__ == "__main__":
    main()