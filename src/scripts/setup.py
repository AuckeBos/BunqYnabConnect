if __name__ == "__main__":
    import _fix_imports

import argparse

parser = argparse.ArgumentParser(description="Setup a part of the library: "
                                             "a) config dir "
                                             "b) supervisor "
                                             "c) continuous deployment")
parser.add_argument("--config", action="store_true", help="Run the config setup")
parser.add_argument("--supervisor", action="store_true", help="Run the supervisor setup")
parser.add_argument("--ci", action="store_true", help="Run the CI setup")


args = parser.parse_args()
if args.config:
    print("Running one-time config setup")
    from _setup.load_config import setup
    setup()
if args.supervisor:
    print("Setting up supervisor")
    from _setup.setup_supervisord import setup
    setup()

else:
    print('Please select a config task')