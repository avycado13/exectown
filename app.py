import logging
from flask import Flask, request, redirect, render_template_string, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///content_store.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

SCHEMA_VERSION = 1


class Content(db.Model):
    __tablename__ = f"content_v{SCHEMA_VERSION}"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def init_db():
    with app.app_context():
        if os.path.exists("content_store.db"):
            logger.info("Database already exists.")
            return
        logger.info("Initializing database...")
        db.create_all()
        logger.info("Database initialized.")


init_db()


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


@app.route("/")
def home_page():
    logger.info("Serving home page.")
    form_html = """<form method="POST" action="/submit">
        <textarea name="handler" rows="10" cols="50">def handler(req):\n    return {\"message\": \"Hello, world!\"}</textarea><br>
        <button type="submit">Deploy!</button>
    </form>"""
    return render_template_string(f"""
        <html>
        <head><title>Val Town Town</title></head>
        <body>
            <h1>Val Town Town</h1>
            <p>Write a Python function and deploy it with one click!</p>
            {form_html}
        </body>
        </html>
    """)


@app.route("/submit", methods=["POST"])
def submit_handler():
    logger.info("Handling form submission.")
    handler = request.form.get("handler")
    if handler:
        logger.info("Received handler code.")
        handler_id = insert_content(handler)
        logger.info(f"Redirecting to handler page for ID: {handler_id}")
        return redirect(f"/handler/{handler_id}")
    logger.warning("No handler code received. Redirecting to home page.")
    return redirect("/")


@app.route("/handler/<int:content_id>")
def handler_page(content_id):
    logger.info(f"Serving handler page for ID: {content_id}")
    handler = get_content(content_id)
    if not handler:
        logger.warning("Handler not found.")
        return "Not Found", 404

    iframe_url = f"/serve/{content_id}"
    return render_template_string(f"""
        <html>
        <head><title>Handler #{content_id}</title></head>
        <body>
            <h1>Python Handler #{content_id}</h1>
            <form method="POST" action="/submit">
                <textarea name="handler" rows="10" cols="50">{handler}</textarea><br>
                <button type="submit">Deploy New Version!</button>
            </form>
            <p>Test: <a href="{iframe_url}">{iframe_url}</a></p>
            <iframe src="{iframe_url}" style="width: 100%; height: 300px;"></iframe>
        </body>
        </html>
    """)


@app.route("/serve/<int:content_id>", methods=["GET", "POST"])
def serve_content(content_id):
    logger.info(f"Serving content for ID: {content_id}")
    handler_code = get_content(content_id)
    if not handler_code:
        logger.warning("Handler code not found.")
        return "Not Found", 404

    try:
        logger.info("Executing handler code.")
        # Define a restricted environment for execution
        safe_globals = {
            "__builtins__": {
                "len": len,
                "range": range,
                "print": print,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "dict": dict,
                "list": list,
                "set": set,
                "tuple": tuple,
                "json": jsonify,
            }
        }
        safe_locals = {}
        exec(handler_code, safe_globals, safe_locals)
        if "handler" not in safe_locals or not callable(safe_locals["handler"]):
            logger.error("Invalid handler function.")
            return "Handler function not defined or invalid.", 400

        # Call the handler with the request as a parameter
        result = safe_locals["handler"](request)

        if isinstance(result, dict):
            logger.info("Handler returned JSON response.")
            return jsonify(result)
        elif isinstance(result, str):
            logger.info("Handler returned HTML response.")
            return result, 200, {"Content-Type": "text/html"}
        else:
            logger.error("Handler returned unsupported response type.")
            return "Unsupported response type.", 500
    except Exception as e:
        logger.error(f"Error executing handler: {e}")
        return f"Error executing handler: {e}", 500


if __name__ == "__main__":
    try:
        logger.info("Starting the Flask server...")
        app.run(host="0.0.0.0", port=5000, debug=False)
    except Exception as e:
        logger.critical(f"Failed to start the server: {e}")
