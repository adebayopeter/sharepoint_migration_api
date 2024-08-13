import pyodbc
from sqlalchemy import create_engine, text
import pandas as pd
from dotenv import load_dotenv
import os
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()


# Spool records to push into sharepoint
def get_document_and_metadata(document_type):
    if document_type == 'dmu':
        document_type = 'DMU'
    else:
        document_type = 'CASE OR BA DOCUMENT'
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
    query = (f"SELECT [FILEID] AS fileid, [RSAPIN] AS pin, [FNAME] AS firstname, "
             f"[LNAME] AS lastname, [MNAME] AS middlename, [PHONE] AS phone, "
             f"[EMPNAME] AS employer_name, [EMPCODE] AS employer_code, "
             f"[DOCTYPE_NAME] AS doc_type, [EDESC] AS 'desc', [FILEITEM] AS file_item, "
             f"[FILENAME] AS filename FROM {query_table}  WHERE [status] IS NULL "
             f"AND [APPLICATION_TYPE] = ?")

    # Use the engine to read the SQL query into a DataFrame
    df = pd.read_sql(query, engine, params=(document_type,))

    return df


def update_document_status(ref_id, doc_link, status, filename):
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
        f"UPDATE {query_table} SET doc_link = :doc_link, "
        f"status = :status WHERE fileid = :ref_id and filename = :filename "
    )

    # Execute the query with parameters
    with engine.connect() as connection:
        connection.execute(query, {
            'doc_link': doc_link,
            'status': status,
            'filename': filename,
            'ref_id': ref_id
        })
        connection.commit()
