if __name__ == "__main__":
    import _fix_imports
from threading import Thread

from model_selection.model_server import ModelServer
from helpers.helpers import load_datasets
import random


# For each set:
# 1. Load a random port to serve it one
# 2. Create a model server
# 3. Set the port to serve on. This also saves it to FS, to look it up for prediction
# 4. Serve async
if __name__ == "__main__":
    sets = load_datasets()
    for set in sets:
        port = random.randint(20000, 30000)
        server = ModelServer(set)
        server.port = port
        Thread(target=server.serve).start()
print('Done!')