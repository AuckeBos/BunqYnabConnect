# Fix relative imports
import sys
sys.path.append("..")
# Fix mlflow save dir
import mlflow
mlflow.set_tracking_uri("http://localhost:10000")
