# run.py
from app import create_app

app = create_app()

if __name__ == "__main__":
    # For dev only — in production use gunicorn or similar
    app.run(host="0.0.0.0", port=5000, debug=True)
