# Fix relative imports
import sys
sys.path.append("..")
# Fix mlflow save dir
try:
    import mlflow
    mlflow.set_tracking_uri("http://localhost:10000")
except:
    pass

