import os
import psycopg2
import pika
import json
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException

app = FastAPI()

# --- Database Connection Details ---
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("DB_HOST")

# --- RabbitMQ Connection Details ---
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS")
QUEUE_NAME = 'dashboard_links_queue'

def get_unique_company_names(table_name: str) -> list[str]:
    """Helper function to fetch all unique company names from a specified table."""
    conn = get_db_connection()
    if conn is None:
        return []
    
    # IMPORTANT: Never use f-strings directly with user input in SQL. 
    # Since table_name is an internal constant, it's safe here, but for columns/tables 
    # always sanitize or use psycopg2.sql if derived from user input.
    query = f"SELECT DISTINCT company_name FROM {table_name} ORDER BY company_name;"
    names = []
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            # Fetch names and flatten the list of dictionaries/tuples
            names = [row['company_name'] for row in cur.fetchall()]
    except Exception as e:
        print(f"Error fetching unique company names: {e}")
    finally:
        if conn:
            conn.close()
    return names

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST,
            cursor_factory=RealDictCursor
        )
        return conn
    except psycopg2.OperationalError:
        return None

@app.get("/")
def read_root():
    return {"status": "API is running"}

@app.get("/live_dashboard_links")
def get_live_dashboard_links_and_populate_queue():
    """
    This function now does two things:
    1. Fetches data from the database.
    2. Publishes that data to the RabbitMQ queue.
    3. Returns the data to the user.
    """
    # --- 1. Fetch data from the database ---
    print("API: Fetching data from database...")
    query = "SELECT * FROM live_dashboard_links;"
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=503, detail="Database connection failed")
    
    links = []
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            links = cur.fetchall()
        print(f"API: Found {len(links)} records in the database.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred fetching data: {e}")
    finally:
        if conn:
            conn.close()

    # --- 2. Publish the data to the queue ---
    if links:
        try:
            print("API: Publishing records to RabbitMQ...")
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials))
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)

            for record in links:
                channel.basic_publish(
                    exchange='',
                    routing_key=QUEUE_NAME,
                    body=json.dumps(record, default=str), # Use default=str for date/time objects
                    properties=pika.BasicProperties(delivery_mode=2)
                )
            connection.close()
            print(f"API: Successfully published {len(links)} records to queue.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to publish to queue: {e}")
            
    # --- 3. Return the data to the user ---
    return {"data": links}

@app.get("/corporate_announcements/{symbol}")
def get_corporate_announcements(symbol: str):
    """
    Fetches corporate announcements for a specific company symbol.
    
    :param symbol: The company's stock symbol (e.g., 'RELIANCE').
    :raises HTTPException 404: If no announcements are found for the given symbol.
    """
    print(f"API: Fetching corporate announcements for symbol: '{symbol}'")
    
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=503, detail="Database connection failed")
    
    announcements = []
    try:
        # We assume the filtering column is named 'symbol' or 'company_symbol' 
        # and use the safe parameterized query format.
        query = "SELECT * FROM corporate_announcements WHERE symbol = %s;"
        
        with conn.cursor() as cur:
            cur.execute(query, (symbol.upper(),)) # Convert to uppercase for robustness
            announcements = cur.fetchall()
        
        if not announcements:
            raise HTTPException(
                status_code=404, 
                detail=f"No corporate announcements found for symbol: '{symbol.upper()}'. Check the symbol or try another."
            )

        print(f"API: Found {len(announcements)} corporate announcement records for '{symbol}'.")
        return {"data": announcements}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred fetching announcement data: {e}")
    finally:
        if conn:
            conn.close()

@app.get("/nifty50_companies")
def get_nift50_companies():
    """
    Fetches all records from the nift50_companies table.
    """
    print("API: Fetching Nifty 50 companies from database...")
    query = "SELECT * FROM nift50_companies;"
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=503, detail="Database connection failed")
    
    companies = []
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            companies = cur.fetchall()
        print(f"API: Found {len(companies)} Nifty 50 company records.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred fetching company data: {e}")
    finally:
        if conn:
            conn.close()
            
    return {"data": companies}

@app.get("/share_holder_pattern")
def get_share_holder_pattern():
    """
    Fetches all records from the share_holder_pattern table.
    """
    print("API: Fetching share holder pattern data from database...")
    query = "SELECT * FROM share_holder_pattern;"
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=503, detail="Database connection failed")
    
    patterns = []
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            patterns = cur.fetchall()
        print(f"API: Found {len(patterns)} share holder pattern records.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred fetching share holder pattern data: {e}")
    finally:
        if conn:
            conn.close()
            
    return {"data": patterns}

@app.get("/employee_reviews/{company_name}")
def get_employee_reviews(company_name: str):
    """
    Fetches employee reviews for a specific company name.
    If the company is not found, it returns an error with a list of available companies.
    """
    print(f"API: Fetching employee reviews for company: '{company_name}'")
    
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=503, detail="Database connection failed")

    # SQL query uses %s placeholder to safely pass the company name
    query = "SELECT * FROM employee_reviews WHERE company_name = %s;"
    
    reviews = []
    try:
        with conn.cursor() as cur:
            # Execute the query with the parameterized value
            cur.execute(query, (company_name,))
            reviews = cur.fetchall()
        
        if not reviews:
            # If no reviews are found, fetch the list of available company names
            available_companies = get_unique_company_names('employee_reviews')
            
            # Raise a 404 (Not Found) error with the list of alternatives
            raise HTTPException(
                status_code=404,
                detail={
                    "error": f"No employee reviews found for company: '{company_name}'.",
                    "suggestion": "Please ensure the company name is spelled correctly.",
                    "available_companies": available_companies
                }
            )
            
        print(f"API: Found {len(reviews)} review records for '{company_name}'.")
        return {"data": reviews}

    except HTTPException:
        # Re-raise the HTTPException defined above (the 404 error)
        raise
    except Exception as e:
        # Handle generic database errors
        raise HTTPException(status_code=500, detail=f"An error occurred fetching reviews: {e}")
    finally:
        if conn:
            conn.close()