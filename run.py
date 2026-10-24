"""Local development server. Use this on Windows before Docker/AWS."""

from app import create_app

app = create_app()

if __name__ == "__main__":
    # 0.0.0.0 lets phones on the same Wi-Fi reach the app during local tests.
    app.run(host="0.0.0.0", port=5000, debug=True)
