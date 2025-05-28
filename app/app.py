from config import create_app
from api.routes import register_routes

# Create Flask app
app = create_app()


# Register routes
register_routes(app)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
