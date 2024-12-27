from app.cli import bp
import os
from app.extensions import db


@bp.cli.command("init")
def init_db():
    """Initialize the database"""
    from app import create_app
    app = create_app()
    with app.app_context():
        if os.path.exists("content_store.db"):
            app.logger.info("Database already exists.")
            return
        app.logger.info("Initializing database...")
        db.create_all()
        app.logger.info("Database initialized.")