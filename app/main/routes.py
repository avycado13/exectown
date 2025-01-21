from app.main import main
from flask import render_template, redirect, request, jsonify, render_template_string
from markupsafe import Markup
import datetime
from app.extensions import logger  # Fix this import
from app.helpers import insert_content, get_content, with_handler_logger, import_remote_package  # Fix this import

@main.route("/")
def index():
    logger.info("Serving home page.")
    return render_template("index.html")

@main.route("/submit", methods=["POST"])
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

@main.route("/handler/<int:content_id>")
def handler_page(content_id):
        logger.info(f"Serving handler page for ID: {content_id}")
        handler = get_content(content_id)
        if not handler:
            logger.warning("Handler not found.")
            return "Not Found", 404

        iframe_url = f"/serve/{content_id}"
        return render_template("handler.html", handler=handler, iframe_url=iframe_url)


@main.route("/serve/<int:content_id>", methods=["GET", "POST"])
@with_handler_logger
def serve_content(content_id,handler_logger):
        logger.info(f"Serving content for ID: {content_id}")
        handler_logger.info(f"Serving content for ID: {content_id}")
        handler_code = get_content(content_id)
        if not handler_code:
            logger.warning("Handler code not found.")
            return "Not Found", 404

        try:
            logger.info("Executing handler code.")
            # Define a restricted environment for execution
            safe_builtins = {
                "len": len, "range": range, "print": print,
                "str": str, "int": int, "float": float,
                "bool": bool, "dict": dict, "list": list,
                "set": set, "tuple": tuple, "sum": sum,
                "min": min, "max": max, "abs": abs,
                "round": round, "type": type
            }
            safe_globals = {
                "__builtins__": safe_builtins,
                "json": jsonify,
                "datetime": datetime,
                "request": request,
                "render_template_string": render_template_string,
                "logger": handler_logger,
                "import_remote_package": import_remote_package
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
                return Markup.escape(result), 200, {"Content-Type": "text/html"}
            else:
                logger.error("Handler returned unsupported response type.")
                return "Unsupported response type.", 500
        except Exception as e:
            logger.error(f"Error executing handler: {e}")
            return f"Error executing handler: {e}", 500