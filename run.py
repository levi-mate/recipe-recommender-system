#!/usr/bin/env python
import sys
import subprocess
import platform
import time
import venv
import importlib.util
import socket
from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
VENV_DIR = BASE_DIR / "venv"


def load_config():
    config_values = {
        "DB_PATH": BACKEND_DIR / "database" / "app_database.db",
        "DATASET_PATH": BACKEND_DIR / "dataset" / "recipes.csv",
        "FLASK_PORT": 5077,
    }
    
    config_file = BACKEND_DIR / "config.py"
    
    if config_file.exists():
        try:
            spec = importlib.util.spec_from_file_location("config", config_file)
            config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config)
            
            if hasattr(config, "DB_PATH"):
                config_values["DB_PATH"] = config.DB_PATH
            if hasattr(config, "DATASET_DIR") and hasattr(config, "DATASET_PATH"):
                config_values["DATASET_PATH"] = config.DATASET_PATH
            elif hasattr(config, "DATASET_DIR"):
                config_values["DATASET_PATH"] = config.DATASET_DIR / "recipes.csv"
            if hasattr(config, "FLASK_PORT"):
                config_values["FLASK_PORT"] = config.FLASK_PORT
                
            print("Loaded settings from config.py")

        except Exception as e:
            print(f"Error loading config.py: {e}")
            print("Using default values")
    else:
        print("Config file not found, using default values")
    
    return config_values


config_values = load_config()
DB_PATH = config_values["DB_PATH"]
DATASET_PATH = config_values["DATASET_PATH"]
FLASK_PORT = config_values["FLASK_PORT"]


def print_section(title):
    print(f"\n{'=' * 80}\n{title}\n{'=' * 80}")


def get_venv_python():
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "python.exe"
    else:
        return VENV_DIR / "bin" / "python"


def check_venv():
    print_section("Checking Python Virtual Environment")
    
    python_path = get_venv_python()
    
    if not python_path.exists():
        print("Virtual environment not found. Creating...")
        
        try:
            venv.create(VENV_DIR, with_pip=True)
            print("Virtual environment created successfully")

        except Exception as e:
            print(f"Failed to create virtual environment: {e}")
            sys.exit(1)
    else:
        print("Virtual environment exists")
    
    return python_path


def install_requirements(python_path):
    print_section("Checking Python Libraries")
    
    req_file = BACKEND_DIR / "requirements.txt"

    if not req_file.exists():
        print("Requirements file not found")
        print(f"Creating requirements.txt")
        
        with open(req_file, "w") as f:
            f.write("""flask==2.2.3
                    flask-cors==3.0.10
                    werkzeug==2.2.3
                    pandas==2.2.3
                    scikit-learn==1.6.1
                    git+https://github.com/daviddavo/lightfm
                    numpy==2.2.4
                    faker==18.4.0
                    pytest==8.3.5
                    pytest-flask==1.3.0
                    """)
    
    try:
        cmd = f'"{python_path}" -c "import flask, pandas, sklearn, lightfm, numpy"'
        subprocess.run(cmd, shell = True, check = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)

        print("Python libraries are already installed")

    except subprocess.CalledProcessError:
        print("Installing Python libraries...")

        try:
            cmd = f'"{python_path}" -m pip install -r "{req_file}"'
            subprocess.run(cmd, shell = True, check = True)
            print("Python libraries installed successfully")

        except subprocess.CalledProcessError as e:
            print(f"Failed to install Python libraries: {e}")
            sys.exit(1)


def check_frontend_deps():
    print_section("Checking Frontend Libraries")
    
    node_modules = FRONTEND_DIR / "node_modules"
    
    if not node_modules.exists():
        print("Frontend libraries not found. Installing...")

        try:
            subprocess.run("npm install", shell = True, check = True, cwd = FRONTEND_DIR)
            print("Frontend libraries installed successfully")

        except subprocess.CalledProcessError as e:
            print(f"Failed to install frontend libraries: {e}")
            print("You need to install Node.js from https://nodejs.org/")

            choice = input("Continue without frontend? [y/N]: ").lower()

            if choice != 'y':
                sys.exit(1)
    else:
        print("Frontend libraries exist")


def check_dataset():
    print_section("Checking Recipe Dataset")
    
    dataset_dir = DATASET_PATH.parent
    dataset_dir.mkdir(parents = True, exist_ok = True)
    
    if not DATASET_PATH.exists():
        print("Dataset not found")
        print(f"The recipe dataset file should be at: {DATASET_PATH}")
        print("\nPlease download the dataset from Kaggle and place it in the correct folder.")

        choice = input("Continue anyway? (database setup will fail) [y/N]: ").lower()

        if choice != 'y':
            sys.exit(1)
    else:
        print("Dataset found")


def setup_database(python_path):
    print_section("Checking Database")
    
    if DB_PATH.exists():
        print("Database found")
        return
    
    print(f"Database not found at {DB_PATH}")
    DB_PATH.parent.mkdir(parents = True, exist_ok = True)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_DIR)
    env["DB_PATH"] = str(DB_PATH)
    env["DATASET_PATH"] = str(DATASET_PATH)
    
    try:
        print("\n[Step 1] Creating database tables...")
        setup_script = BACKEND_DIR / "setup" / "setup_db.py"
        subprocess.run([str(python_path), str(setup_script)], check = True, cwd = str(BACKEND_DIR), env = env)
        
        print("\n[Step 2] Loading recipes data from dataset...")
        setup_script = BACKEND_DIR / "setup" / "load_recipes.py"
        subprocess.run([str(python_path), str(setup_script)], check = True, cwd = str(BACKEND_DIR), env = env)
        
        print("\n[Step 3] Extracting and loading ingredients from dataset...")
        setup_script = BACKEND_DIR / "setup" / "extract_ingredients.py"
        subprocess.run([str(python_path), str(setup_script)], check = True, cwd = str(BACKEND_DIR), env = env)
        
        print("\n[Step 4] Generating fake user data...")
        setup_script = BACKEND_DIR / "setup" / "generate_fake_data.py"
        subprocess.run([str(python_path), str(setup_script)], check = True, cwd = str(BACKEND_DIR), env = env)
        
        print("Database setup completed successfully")

    except subprocess.CalledProcessError as e:
        print(f"Failed to set up database: {e}")
        sys.exit(1)


def check_port_in_use(port, timeout = 1):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)

    try:
        s.bind(("localhost", port))
        s.close()

        return False
    
    except (socket.error, OSError):
        return True
    
    finally:
        s.close()


def kill_process_on_port(port):
    if platform.system() == 'Windows':
        try:
            result = subprocess.run(f"netstat -ano | findstr :{port}", shell = True, capture_output = True, text = True)
            
            for line in result.stdout.strip().split('\n'):
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.strip().split()

                    if parts:
                        pid = parts[-1]

                        print(f"Killing process with PID {pid} using port {port}")
                        subprocess.run(f"taskkill /F /PID {pid}", shell = True)

                        return True
                    
            return False
        
        except Exception as e:
            print(f"Error killing process on port {port}: {e}")

            return False
    else:
        print("Port cleanup only supported on Windows")

        return False


def start_servers(python_path):
    print_section("Starting Application Servers")
    
    print(f"Checking if port {FLASK_PORT} is already in use...")
    
    if check_port_in_use(FLASK_PORT):
        print(f"WARNING: Port {FLASK_PORT} is already in use!")
        print("This could mean the backend server is already running from a previous session.")

        choice = input("Do you want to try killing the process using this port? (y/N): ").lower()
        
        if choice == 'y':
            if kill_process_on_port(FLASK_PORT):
                print(f"Successfully freed port {FLASK_PORT}")
                time.sleep(1)
            else:
                print(f"Failed to free port {FLASK_PORT}")
                choice = input("Continue anyway? (y/N): ").lower()

                if choice != 'y':
                    print("Exiting... Please close any running servers and try again.")
                    sys.exit(1)
        else:
            choice = input("Continue without starting backend server? (y/N): ").lower()

            if choice != 'y':
                print("Exiting... Please close any running servers and try again.")
                sys.exit(1)
    
    print("Starting backend server...")
    
    if platform.system() == "Windows":
        backend_process = subprocess.Popen(f'start "Recipe Backend" /min cmd /c "{python_path}" webapp.py', shell = True, cwd = str(BACKEND_DIR))
    else:
        backend_process = subprocess.Popen([str(python_path), "webapp.py"], cwd = str(BACKEND_DIR))
    
    print(f"Waiting for backend server to start on port {FLASK_PORT}...")

    max_retries = 15

    for i in range(max_retries):
        time.sleep(1)

        if check_port_in_use(FLASK_PORT):
            print(f"Backend server started successfully (detected after {i + 1} seconds)")

            break

        print(".", end = "", flush = True)
    else:
        print("\nWARNING: Could not confirm backend server started.")
        print("The server may still be starting up or there might be an issue.")
        print("Check the backend terminal for more information.")

        choice = input("Continue with frontend startup? (y/N): ").lower()

        if choice != 'y':
            print("Exiting...")
            sys.exit(1)
    
    print("Starting frontend server...")

    if platform.system() == "Windows":
        frontend_cmd = 'start "Recipe Frontend" /min cmd /c npm run dev'
        frontend_process = subprocess.Popen(frontend_cmd, shell = True, cwd = str(FRONTEND_DIR))
    else:
        frontend_process = subprocess.Popen(["npm", "run", "dev"], cwd = str(FRONTEND_DIR))
    
    print("\n*** Application started ***\n")
    print("- Frontend: http://localhost:5173")
    print(f"- Backend: http://localhost:{FLASK_PORT}\n")
    print("You can access the webapp by going to http://localhost:5173 in your browser")
    print("\nServers are now running in separate terminals\n")
    print("You can use 'python run.py --cleanup' to kill the backend server and free the port\n")
    print("You can use 'python run.py --test' to run the automated tests\n")


def run_tests(python_path):
    print_section("Running Backend Tests")
    
    test_runner = BACKEND_DIR / "tests" / "run_tests.py"
    
    cmd = [str(python_path), str(test_runner)]
    subprocess.run(cmd, cwd = str(BACKEND_DIR))


def main():
    print_section("Recipe Recommendation System")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--cleanup':
        print(f"Attempting to free port {FLASK_PORT}...")

        if kill_process_on_port(FLASK_PORT):
            print(f"Successfully freed port {FLASK_PORT}")
        else:
            print(f"No process found using port {FLASK_PORT}")

        sys.exit(0)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        python_path = check_venv()
        run_tests(python_path)

        sys.exit(0)

    python_path = check_venv()
    install_requirements(python_path)
    check_frontend_deps()
    check_dataset()
    setup_database(python_path)
    start_servers(python_path)


if __name__ == "__main__":
    main()