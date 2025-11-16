"""FastAPI integration example."""

try:
    from fastapi import FastAPI
    from toonverter.integrations import TOONResponse

    app = FastAPI(title="TOON Converter API Example")

    @app.get("/users", response_class=TOONResponse)
    async def get_users():
        """Return users in TOON format (token-optimized)."""
        users = [
            {"id": 1, "name": "Alice", "email": "alice@example.com", "active": True},
            {"id": 2, "name": "Bob", "email": "bob@example.com", "active": True},
            {"id": 3, "name": "Charlie", "email": "charlie@example.com", "active": False},
        ]
        # Automatically encoded as TOON with proper content-type
        return users

    @app.get("/stats", response_class=TOONResponse)
    async def get_stats():
        """Return statistics in TOON format."""
        return {
            "total_users": 1000,
            "active_users": 750,
            "requests_today": 5432,
            "average_response_time_ms": 45.7,
        }

    if __name__ == "__main__":
        import uvicorn

        print("=" * 60)
        print("FastAPI + TOON Converter Example")
        print("=" * 60)
        print("\nStarting server...")
        print("Visit: http://127.0.0.1:8000/users")
        print("Or: http://127.0.0.1:8000/stats")
        print("\nPress Ctrl+C to stop")
        print()

        uvicorn.run(app, host="127.0.0.1", port=8000)

except ImportError:
    print("This example requires fastapi and uvicorn.")
    print("Install with: pip install toonverter[integrations] uvicorn")
