if __name__ == "__main__":
    import _fix_imports

print("Running one-time config setup")
from _setup.load_config import setup
setup()