import pyodbc
from sqlalchemy import create_engine, text
import pandas as pd
from dotenv import load_dotenv
import os
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()


# Spool records to push into sharepoint
def get_images_and_metadata():
    # Create the connection string and  URL-encode the username and password
    username = quote_plus(os.getenv('DB_USERNAME'))
    password = quote_plus(os.getenv('DB_PASSWORD'))
    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_DATABASE')
    driver = quote_plus(os.getenv('DB_DRIVER'))

    # Create the connection string
    conn_str = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver}"

    # Create the SQLAlchemy engine
    engine = create_engine(conn_str)

    query_table = os.getenv('DB_TABLE_1')
    query = (f"SELECT [RSAPIN] AS pin, [FILEID] AS fileid, [EDESC] AS 'desc', "
             f"[DOCTYPE] AS doctype, [DOCTYPE DESCRIPTION] AS doctype_desc, "
             f"[FILEITEM] AS file_item, [FILENAME] AS filename FROM {query_table} WHERE [status] IS NULL")

    # Use the engine to read the SQL query into a DataFrame
    df = pd.read_sql(query, engine)

    return df


def update_image_status(ref_id, image_link, status, filename):
    # URL-encode the username and password
    username = quote_plus(os.getenv('DB_USERNAME'))
    password = quote_plus(os.getenv('DB_PASSWORD'))
    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_DATABASE')
    driver = quote_plus(os.getenv('DB_DRIVER'))

    # Create the connection string
    conn_str = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver}"

    # Create the SQLAlchemy engine
    engine = create_engine(conn_str)

    query_table = os.getenv('DB_TABLE_1')

    # Define the query using SQLAlchemy's text function
    query = text(
        f"UPDATE {query_table} SET image_link = :image_link, "
        f"status = :status WHERE fileid = :ref_id and filename = :filename "
    )

    # Execute the query with parameters
    with engine.connect() as connection:
        connection.execute(query, {
            'image_link': image_link,
            'status': status,
            'filename': filename,
            'ref_id': ref_id
        })
        connection.commit()
