from flask_sqlalchemy import SQLAlchemy
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a SQLAlchemy instance
db = SQLAlchemy()