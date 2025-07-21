#!/usr/bin/env python3
"""
Smart City Garbage Detection System Setup Script
This script sets up the complete Django backend system
"""

import os
import sys
import subprocess
import django
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error in {description}: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return None

def setup_django():
    """Setup Django environment"""
    print("🚀 Setting up Smart City Garbage Detection System")
    print("=" * 60)
    
    # Install requirements
    if run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        print("✅ All dependencies installed")
    else:
        print("❌ Failed to install dependencies")
        return False
    
    # Create Django project structure
    print("\n📁 Creating Django project structure...")
    
    # Create necessary directories
    directories = [
        'media/videos',
        'media/frames', 
        'media/annotated',
        'media/garbage_locations',
        'media/completed',
        'media/activities',
        'static',
        'staticfiles',
        'templates',
        'models',  # For YOLO model files
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_city.settings')
    django.setup()
    
    # Create Django apps
    apps = ['garbage_detection', 'dashboard', 'api']
    for app in apps:
        if not os.path.exists(app):
            run_command(f"python manage.py startapp {app}", f"Creating Django app: {app}")
    
    # Run migrations
    run_command("python manage.py makemigrations", "Creating database migrations")
    run_command("python manage.py migrate", "Applying database migrations")
    
    # Create superuser (optional)
    print("\n👤 Creating admin superuser...")
    print("You can create an admin user to access the Django admin panel")
    try:
        subprocess.run([
            sys.executable, "manage.py", "createsuperuser", 
            "--username", "admin", 
            "--email", "admin@smartcity.com"
        ], check=False)
    except:
        print("⚠️  Superuser creation skipped (you can create one later)")
    
    # Collect static files
    run_command("python manage.py collectstatic --noinput", "Collecting static files")
    
    return True

def check_yolo_model():
    """Check if YOLO model exists"""
    model_path = "models/garbage_detection.pt"
    if os.path.exists(model_path):
        print(f"✅ YOLO model found at {model_path}")
        return True
    else:
        print(f"⚠️  YOLO model not found at {model_path}")
        print("   The system will use default YOLOv8 model")
        print("   Place your custom garbage detection model at models/garbage_detection.pt")
        return False

def start_services():
    """Start required services"""
    print("\n🔧 Starting services...")
    
    # Check if Redis is running (for Celery)
    redis_check = run_command("redis-cli ping", "Checking Redis connection")
    if redis_check and "PONG" in redis_check:
        print("✅ Redis is running")
    else:
        print("⚠️  Redis is not running. Install and start Redis for background processing:")
        print("   - Ubuntu: sudo apt install redis-server && sudo systemctl start redis")
        print("   - macOS: brew install redis && brew services start redis")
        print("   - Windows: Download from https://redis.io/download")

def display_urls():
    """Display important URLs"""
    print("\n🌐 Important URLs:")
    print("=" * 40)
    print("🏠 Django Admin:     http://localhost:8000/admin/")
    print("📊 User Dashboard:   http://localhost:8000/dashboard/")
    print("🔧 Admin Dashboard:  http://localhost:8000/admin-dashboard/")
    print("🗺️  Map View:        http://localhost:8000/map/")
    print("📱 API Docs:         http://localhost:8000/api/docs/")
    print("💚 Health Check:     http://localhost:8000/api/health/")

def main():
    """Main setup function"""
    print("🏙️  Smart City Garbage Detection System")
    print("🗑️  AI-Powered Waste Management Platform")
    print("=" * 60)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Setup Django
    if not setup_django():
        print("❌ Django setup failed")
        sys.exit(1)
    
    # Check YOLO model
    check_yolo_model()
    
    # Start services
    start_services()
    
    # Display URLs
    display_urls()
    
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("\n📱 Android App Configuration:")
    print("   Update NetworkManager.kt with your server IP:")
    print("   private const val BASE_URL = \"http://YOUR_IP:8000/\"")
    
    print("\n🚀 To start the server:")
    print("   python manage.py runserver 0.0.0.0:8000")
    
    print("\n🔄 To start background processing (in another terminal):")
    print("   celery -A smart_city worker --loglevel=info")
    
    print("\n📖 Default Login (if superuser created):")
    print("   Username: admin")
    print("   Password: (as entered during setup)")
    
    # Ask if user wants to start the server
    start_server = input("\n❓ Start Django server now? (y/n): ").lower().strip()
    if start_server == 'y':
        print("\n🚀 Starting Django server...")
        print("Press Ctrl+C to stop the server")
        try:
            subprocess.run([
                sys.executable, "manage.py", "runserver", "0.0.0.0:8000"
            ])
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")

if __name__ == "__main__":
    main()