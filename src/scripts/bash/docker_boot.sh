#!/usr/bin/env sh
cd /app
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
source $HOME/.poetry/env
poetry install .
echo 'ok!'