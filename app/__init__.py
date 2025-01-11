from flask import Flask
from app.extensions import logger, db
import os
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # Register blueprints
    from app.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.cli import bp as cli_blueprint
    app.register_blueprint(cli_blueprint)

    def init_db():
        with app.app_context():
            if os.path.exists("content_store.db"):
                logger.info("Database already exists.")
                return
            logger.info("Initializing database...")
            db.create_all()
            logger.info("Database initialized.")

    # Initialize database
    # @app.before_first_request()
    # def before_first_request():
    #     try:
    #         init_db()
    #     except Exception as e:
    #         logger.error(f"Failed to initialize database: {e}")
    init_db()
    return app

if __name__ == "__main__":
    app = create_app()
    try:
        app.logger.info("Starting the Flask server...")
        app.run(host="0.0.0.0", port=5000, debug=False)
    except Exception as e:
        app.logger.critical(f"Failed to start the server: {e}")
