#!/usr/bin/env bash
gunicorn app.main:app -c gunicorn.conf.py
