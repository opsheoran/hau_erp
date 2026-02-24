from app import app
import os

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5012))
    debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
    host = os.getenv('HOST', '127.0.0.1')
    app.run(debug=debug_mode, host=host, port=port)
