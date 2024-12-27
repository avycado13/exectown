from app.extensions import db,logger
from app.models import Content
import logging
from functools import wraps
import httpimport


def insert_content(body):
        logger.info(f"Inserting content into the database: {body[:30]}...")
        content = Content(body=body)
        db.session.add(content)
        db.session.commit()
        logger.info(f"Content inserted with ID: {content.id}")
        return content.id

def get_content(content_id):
        logger.info(f"Fetching content with ID: {content_id}...")
        content = Content.query.get(content_id)
        if content:
            logger.info(f"Content fetched: {content.body[:30]}...")
        else:
            logger.warning("No content found.")
        return content.body if content else None


# Handler logging functions

def get_handler_logger(handler_id):
    """Create a dedicated logger for a specific handler"""
    # Create a new logger for this handler
    logger = logging.getLogger(f"handler_{handler_id}")
    
    # Only add handler if logger doesn't already have handlers
    if not logger.handlers:
        # Set log level
        logger.setLevel(logging.INFO)
        
        # Create file handler
        handler = logging.FileHandler(f"logs/handler_{handler_id}.log",mode="a+")
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
    
    return logger

def with_handler_logger(f):
    """Decorator to inject a handler-specific logger"""
    @wraps(f)
    def wrapper(content_id, *args, **kwargs):
        handler_logger = get_handler_logger(content_id)
        return f(content_id, handler_logger, *args, **kwargs)
    return wrapper

def import_remote_package(url, package_name):
    """
    Imports a Python package or module from a remote URL using httpimport.

    Args:
        url (str): The URL where the package/module is hosted.
        package_name (str): The name of the package/module to import.

    Returns:
        module: The imported module object.

    Raises:
        ImportError: If the module cannot be imported.
    """
    try:
        with httpimport.remote_repo(url):
            module = __import__(package_name)
            return module
    except Exception as e:
        raise ImportError(f"Failed to import module '{package_name}' from URL '{url}': {e}")
