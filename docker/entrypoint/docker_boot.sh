#!/usr/bin/env sh
# If supervisor setup had never been ran, do so

/usr/local/bin/supervisord
#if [ ! -d "/supervisor/supervisord.conf" ]
#then
#  echo "Running the one-time supervisor setup"
#  cd /app/scripts
#  python setup.py --supervisor
#fi
# Create cache dir, if doesnt exist yet
mkdir -p /cache
echo 'Done!'
tail -f /dev/null
#touch /test.txt
#mlflow server --host=0.0.0.0 --port=10000 --backend-store-uri sqlite:///../../mlflow.db --default-artifact-root artifacts