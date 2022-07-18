#Deriving the latest base image
FROM python:latest
#Labels as key value pair
LABEL Maintainer="Aucke Bos"

WORKDIR /app
# Install poetry
RUN pip install poetry


COPY pyproject.toml poetry.lock /app/
RUN apt-get update -y
RUN apt-get install -y python3-scipy
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

#CMD instruction should be used to run the software
#contained by your image, along with any arguments.

#CMD [ "python", "./test.py"]