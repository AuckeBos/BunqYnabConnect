#!/usr/bin/env sh
# CD into the scripts dir
cd /app/scripts/bash
# Start supervisor
/usr/local/bin/supervisord -c /supervisord.conf
# Start cron
cron
# Start server that receives transactions
./start_transactions_server.sh
# Serve the existing models
./serve_models.sh
# Start mlflow server
mlflow server --host=0.0.0.0 --port=10000 --backend-store-uri sqlite:///../../mlflow.db --default-artifact-root artifacts