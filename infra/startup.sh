#!/bin/bash
set -e
export PYTHONPATH=./src
python -m alembic upgrade head
exec python -m uvicorn wyrmwood_coffee.main:app --host 0.0.0.0 --port 8000
