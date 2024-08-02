# FastAPI Application with SQL Server Integration and NTLM-authenticated SharePoint On-premises File Upload

## Overview

This project is a FastAPI application that integrates with SQL Server to retrieve images and their metadata, uploads the images to a SharePoint on-premises document library using NTLM authentication, and updates the SQL Server database with the new SharePoint links and statuses.

## Features

- Environment variables management using `python-dotenv`
- Database connection and data retrieval using `pyodbc`
- Image upload to SharePoint on-premises using `Office365-REST-Python-Client` with NTLM authentication
- Metadata update in SQL Server
- FastAPI endpoints to handle image upload and metadata update

## Prerequisites

- Python 3.7+
- Access to a SQL Server database
- Access to a SharePoint on-premises site with NTLM authentication

## Setup

1. Clone the repository:

    ```sh
    git clone <repository_url>
    cd <repository_name>
    ```

2. Create a virtual environment and activate it:

    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. Install the required packages:

    ```sh
    pip install -r requirements.txt
    ```

4. Create a `.env` file in the root directory and add your configuration:

    ```env
    DB_DRIVER=ODBC Driver 17 for SQL Server
    DB_SERVER=your_server_name
    DB_DATABASE=your_database_name
    DB_USERNAME=your_username
    DB_PASSWORD=your_password

    SHAREPOINT_SITE_URL=http://your-sharepoint-site-url
    SHAREPOINT_USERNAME=your_domain\\your_sharepoint_username
    SHAREPOINT_PASSWORD=your_sharepoint_password
    SHAREPOINT_DOC_LIBRARY=YourDocumentLibrary
    DB_TABLE_1=your_table_name
    ```

5. Run the FastAPI application:

    ```sh
    uvicorn main:app --reload
    ```

6. Access the API documentation at `http://127.0.0.1:8000/docs`

## Project Structure

- `main.py`: The main FastAPI application file that handles the endpoints.
- `database.py`: Contains functions for database connection, data retrieval, and status update.
- `.env`: Environment variables configuration file (not included in the repository).
- `requirements.txt`: List of required Python packages.

## Endpoints

- **POST /upload_images**: Retrieves images and metadata from SQL Server, uploads the images to SharePoint, and updates the SQL Server database with the new links and statuses.

## License
This project is licensed under [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)