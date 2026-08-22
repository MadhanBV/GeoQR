import os
from flask import Flask, render_template_string, render_template, redirect, url_for
from config import Config


def create_app(config_class=Config):
    """
    Application Factory for GeoQR.
    Initializes Flask app, registers blueprints, and sets up global handlers.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register Blueprints (will be imported and attached as we build each module)
    try:
        from routes.host_routes import host_bp
        app.register_blueprint(host_bp)
    except ImportError:
        pass

    try:
        from routes.student_routes import student_bp
        app.register_blueprint(student_bp)
    except ImportError:
        pass

    @app.route("/")
    def index():
        """Root landing route: redirects to event creation or host dashboard."""
        return redirect(url_for("host.create_event_page") if "host.create_event_page" in app.view_functions else "/host/create")

    @app.route("/health")
    def health_check():
        """Health check endpoint to verify backend status."""
        return {
            "status": "healthy",
            "service": "GeoQR Attendance System",
            "version": "1.0.0"
        }

    return app


if __name__ == "__main__":
    app = create_app()
    print(f"[GeoQR] Server running at http://{app.config['HOST']}:{app.config['PORT']}")
    app.run(
        host=app.config["HOST"],
        port=app.config["PORT"],
        debug=app.config["DEBUG"]
    )
