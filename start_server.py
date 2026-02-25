import os
from backend.app import create_app

os.environ.setdefault('FLASK_ENV', 'production')

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)
