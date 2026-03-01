web: gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT scripts.api_server:app
telegram: python scripts/telegram_commander_pro.py
websocket: python scripts/websocket_server.py
