from app.extensions import db
from flask import current_app
import datetime

class Content(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        body = db.Column(db.Text, nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.datetime.now(datetime.timezone.utc))

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.__tablename__ = f"content_v{current_app.config['SCHEMA_VERSION']}"