if __name__ == "__main__":
    import _fix_imports
from model_selection.model_server import ModelServer
import random
from train_models import train_models
from helpers.helpers import (
    load_datasets,
    mlflow_is_initialized,
    log,
    should_restart_model_serving, RESTART_MODEL_SERVING_FILE,
)
from time import sleep
import multiprocessing
import os
from multiprocessing import Process
from typing import List

threads: List[Process] = []

def serve_models():
    """
    For each set:
    1. Load a random port to serve it one
    2. Create a model server
    3. Set the port to serve on. This also saves it to FS, to look it up for prediction
    4. Serve async
    """
    global threads
    for thread in threads:
        thread.terminate()
    threads = []
    log("Serving models")
    sets = load_datasets()
    for set in sets:
        port = random.randint(20000, 30000)
        server = ModelServer(set)
        server.port = port
        thread = multiprocessing.Process(target=server.serve, args=())
        thread.start()
        threads.append(thread)


# If mlflow has not been initialized (eg this is the first time the models are
#     served), train the models, which will initialize mlflow
if __name__ == "__main__":
    if not mlflow_is_initialized():
        print("Training models")
        train_models()
        print("Models trained")
    # Start serving
    serve_models()
    # Wait indefinitely.
    while True:
        sleep(10)
        # If should restart, restart
        if should_restart_model_serving():
            os.remove(RESTART_MODEL_SERVING_FILE)
            serve_models()
