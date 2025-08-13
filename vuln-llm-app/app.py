import os
from flask import Flask

# Local imports
from routes.challenges import bp as challenges_bp


def create_app() -> Flask:
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
    app.config['SECRET_KEY'] = os.getenv('GPT5_SECRET_KEY', 'gpt5-secret')

    # Register challenge UI blueprint at root
    app.register_blueprint(challenges_bp, url_prefix='/')
    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('GPT5_PORT', '5002'))
    app.run(host='0.0.0.0', port=port, debug=True)
