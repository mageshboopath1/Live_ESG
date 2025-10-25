import os
import time
import sys
from fastapi import FastAPI, HTTPException, status
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConfigurationError
from typing import List, Dict, Any
import json
from bson import json_util # Used to serialize MongoDB BSON types (like ObjectIDs)

# --- Configuration ---
# MONGO_URI from docker-compose, accessible via service name
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo_db:27017/") 
MONGO_DB_NAME = os.getenv("MONGO_DB", "esg_data")
MONGO_COLLECTION_NAME = 'pollution_records' 

app = FastAPI(title="Pollution Data API")
mongo_client: MongoClient = None
db = None

def connect_to_mongodb():
    """
    Initializes the MongoDB connection and handles retries.
    """
    global mongo_client, db
    
    print(f"API: Attempting to connect to MongoDB at {MONGO_URI}...")
    max_retries = 10
    
    for i in range(max_retries):
        try:
            # Use connect=False initially, then explicitly check connection, disable TLS
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, tls=False, connect=False)
            client.admin.command('ping') # Force connection and check
            
            mongo_client = client
            db = mongo_client[MONGO_DB_NAME]
            print("API: Successfully connected to MongoDB.")
            return
        except ServerSelectionTimeoutError as e:
            print(f"MongoDB Connection failed. Retrying in 5 seconds... ({i+1}/{max_retries}).")
            time.sleep(5)
        except Exception as e:
            print(f"An unexpected error occurred during MongoDB connection: {e}")
            time.sleep(5)
            
    print("API: Failed to connect to MongoDB after multiple retries. Exiting.")
    sys.exit(1)


@app.on_event("startup")
async def startup_event():
    """
    Executed when the application starts up.
    """
    # Delay to allow MongoDB container to fully initialize
    time.sleep(5)
    connect_to_mongodb()
    
@app.on_event("shutdown")
def shutdown_event():
    """
    Executed when the application shuts down.
    """
    if mongo_client:
        mongo_client.close()
        print("API: MongoDB connection closed.")

# --- Endpoints ---

@app.get("/", status_code=status.HTTP_200_OK)
def read_root():
    """Health check endpoint."""
    # Check client health, not database object truthiness
    if mongo_client is None:
        raise HTTPException(status_code=503, detail="API is waiting for database connection.")
    return {"message": "Pollution Data API is operational."}

@app.get("/pollution_records", response_model=List[Dict[str, Any]])
def get_recent_records(limit: int = 100):
    """
    Fetches the latest pollution records from MongoDB, sorted by scrape time.
    """
    # FIX: Change 'if not db:' to the correct comparison 'if db is None:'
    if db is None: 
        raise HTTPException(status_code=503, detail="Database not connected.")
    
    try:
        collection = db[MONGO_COLLECTION_NAME]
        
        # Query: Sort by the custom datetime field (newest first) and limit
        # The data is already saved with the 'scraped_datetime_utc' field.
        records = collection.find(
            {}
        ).sort("scraped_datetime_utc", -1).limit(limit)
        
        # Use json_util to correctly serialize MongoDB's ObjectId and BSON types
        data = json.loads(json_util.dumps(list(records)))
        
        return data

    except Exception as e:
        print(f"Error querying MongoDB: {e}")
        # Re-raise the HTTPException defined in the original code, but ensure we log the error
        raise HTTPException(status_code=500, detail="Internal server error during data retrieval.")