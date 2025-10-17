import subprocess
import time
import logging
import os
import signal

from config import svc_configs

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

configs = svc_configs()
default_settings = configs["default"]["settings"]

# Configuration for instance management
NUM_INSTANCES = default_settings.get("max_instance", 5)
BASE_PORT = default_settings.get("base_port", 10501)

# Get the Python interpreter path from the virtual environment
python_executable = os.path.join("venv", "Scripts", "python.exe") if os.name == 'nt' else os.path.join("venv", "bin", "python")

# Start instances
processes = []

try:
    # Start the WebSocket server
    # ws_process = subprocess.Popen([python_executable, "websocket.py"])
    # processes.append(ws_process)
    # logging.info("Started WebSocket server.")

    for i in range(NUM_INSTANCES):
        port = BASE_PORT + i
        process = subprocess.Popen([python_executable, "main.py", str(port)])
        processes.append(process)
        logging.info(f"Started instance {i+1} on port {port}")
        time.sleep(1)  # Small delay to stagger startup

    # Wait for instances to run or handle shutdown logic here
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("\nShutting down instances gracefully...")
        # Send a termination signal to all processes
        for process in processes:
            os.kill(process.pid, signal.SIGTERM)  # Send a termination signal
            process.wait()  # Wait for the process to terminate
        logging.info("All instances have been shut down.")

except Exception as e:
    logging.error(f"An error occurred: {e}")

finally:
    # Ensure all processes are terminated on exit
    for process in processes:
        if process.poll() is None:  # If the process is still running
            process.terminate()  # Ensure it gets terminated
