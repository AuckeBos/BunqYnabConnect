#!/usr/bin/env sh
cd /app/scripts/bash
# Start supervisor
/usr/local/bin/supervisord -c /supervisord.conf
# Start cron
cron
# Start mlflow server, detached
mlflow server --host=0.0.0.0 --port=10000 --backend-store-uri sqlite:////mlflow.db --default-artifact-root artifacts &>/logs/mlflow.log &

# Serve the existing models. Run forever
./serve_models.sh