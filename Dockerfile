FROM python:3.8
LABEL Maintainer="Aucke Bos"

# Expose port. For transactions server
EXPOSE 9888/tcp

# Expose port for mlflow ui, and supervisord
EXPOSE 10000/tcp
EXPOSE 10001/tcp

RUN mkdir /app
WORKDIR /app

# Install poetry, and install dependencies without creating a venv
RUN pip install poetry
COPY pyproject.toml poetry.lock /app/
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

# Install crontab, create cronfile
RUN apt-get update -y
RUN apt-get install -y cron

# “At 06:00 on Sunday.”, retrain the models
RUN (echo "0 6 * * 7 cd /app/scripts/bash && ./train_models.sh" | crontab -u root -)

# Copy supervisor file
COPY docker/entrypoint/supervisord.conf /supervisord.conf

# Copy config data
COPY config /config

# Create /cache folder
RUN mkdir /cache

# Create log dir
RUN mkdir /logs
RUN mkdir /logs/supervisor
RUN mkdir /logs/supervisor/childlogs

# Copy boot script, and set entrypoint
COPY docker/entrypoint/docker_boot.sh /docker_boot.sh
# Set entrypoint
ENTRYPOINT "/docker_boot.sh"