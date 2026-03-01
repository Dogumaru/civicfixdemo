"""
CivicFix Setup Helper
Run: python setup.py
"""
import subprocess
import sys
import os


def run(cmd, cwd=None):
    print(f"\n>>> {cmd}")
    subprocess.run(cmd, shell=True, cwd=cwd, check=True)


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root, "backend")
    frontend_dir = os.path.join(root, "frontend")

    print("=" * 50)
    print("  CivicFix Setup")
    print("=" * 50)

    # Backend
    print("\n[1/3] Installing Python dependencies...")
    run(f"{sys.executable} -m pip install -r requirements.txt", cwd=backend_dir)

    # Frontend
    print("\n[2/3] Installing Node.js dependencies...")
    run("npm install", cwd=frontend_dir)

    print("\n[3/3] Setup complete!")
    print("""
To start the app:

  Terminal 1 (Backend):
    cd backend
    uvicorn app.main:app --reload --port 8000

  Terminal 2 (Frontend):
    cd frontend
    npm run dev

  Then open: http://localhost:5173

NOTE: Make sure PostgreSQL is running with:
  - Database: civicfix
  - User: civicfix
  - Password: civicfix
  - Port: 5432
""")


if __name__ == "__main__":
    main()
