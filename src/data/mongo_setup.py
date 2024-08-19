import os

from mongoengine import connect
from dotenv import load_dotenv
load_dotenv()


def global_init():
    try:
        connect(
            db=os.getenv('MONGO_DB_NAME', 'your_db_name'),
            alias='core',
            host='localhost',
            port=int(os.getenv("PORT")),
            serverSelectionTimeoutMS=5000  # 5-second timeout
        )
        print("MongoDB connection established.")
    except ConnectionError as e:
        print(f"Could not connect to MongoDB: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
