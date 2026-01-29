import os


def main() -> int:
    # Optional: load local .env (ignored by git)
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv()
    except Exception:
        pass

    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("MONGO_URI is not set. Create a local .env (ignored) or export MONGO_URI.")
        return 2

    try:
        from pymongo import MongoClient  # type: ignore
    except Exception as e:
        print("Missing dependency: pymongo. Install with: python -m pip install pymongo")
        print(f"Import error: {e}")
        return 3

    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=8000)
    try:
        client.admin.command("ping")
        print("MongoDB ping: OK")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
