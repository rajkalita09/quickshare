"""WSGI entrypoint used by Gunicorn."""

from app import create_app

app = create_app()
