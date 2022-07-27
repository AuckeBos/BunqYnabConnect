FROM python:3.8
LABEL Maintainer="Aucke Bos"

# Copy src
COPY src /app

WORKDIR /app

# Install poetry, and install dependencies without creating a venv
RUN pip install poetry
COPY pyproject.toml poetry.lock /app/
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

# Install crontab, create empty cron
RUN apt-get update -y
RUN apt-get install -y cron
RUN touch empty_cron.txt
RUN crontab empty_cron.txt

# Copy supervisor folder
COPY supervisor/supervisord.conf /usr/local/etc/supervisord.conf
# Copy docker entrypoint data
COPY docker/entrypoint /entrypoint
# Copy config data
COPY config /config

# Set entrypoint
ENTRYPOINT "/entrypoint/docker_boot.sh"