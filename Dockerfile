FROM python:3.8
LABEL Maintainer="Aucke Bos"

# Copy src
COPY src /app
WORKDIR /app

# Install poetry, and install dependencies without creating a venv
RUN pip install poetry
COPY pyproject.toml poetry.lock /app/
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

# Install crontab, create cronfile
RUN apt-get update -y
RUN apt-get install -y cron
COPY docker/entrypoint/cronfile /etc/cron.d/cronfile

# Copy boot script
COPY docker/entrypoint/docker_boot.sh /docker_boot.sh
# Copy supervisor file
COPY docker/entrypoint/supervisord.conf /supervisord.conf

# Copy config data
COPY config /config

# Create /cache folder
RUN mkdir /cache

# Prevent access issues on host
RUN mkdir /logs
RUN mkdir /logs/supervisor
RUN mkdir /logs/supervisor/childlogs
RUN chmod -R 777 /logs

# TEMP
COPY mlflow.db /mlflow.db
# Set entrypoint
ENTRYPOINT "/docker_boot.sh"