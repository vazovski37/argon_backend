"""
Flask Application Entry Point
"""
import os
from app import create_app
from app.config import DevelopmentConfig, ProductionConfig

# Determine environment
env = os.getenv('FLASK_ENV', 'development')

if env == 'production':
    config = ProductionConfig
else:
    config = DevelopmentConfig

app = create_app(config)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = env != 'production'
    
    print(f"🚀 Starting Argonauts Backend on port {port}")
    print(f"📊 Environment: {env}")
    print(f"🔗 API URL: http://localhost:{port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)





