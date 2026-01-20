#!/bin/bash
# Calculate number of workers: (2 x cores) + 1
# This command runs the app using Gunicorn and Uvicorn's worker class
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-log - \
  --error-log -