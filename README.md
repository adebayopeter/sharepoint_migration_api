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

1. **Clone the repository:**

   ```sh
   git clone <repository_url>
   cd <repository_name>

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
    DB_DRIVER='ODBC Driver 17 for SQL Server'
    DB_SERVER=your_server_name
    DB_DATABASE=your_database_name
    DB_USERNAME=your_username
    DB_PASSWORD=your_password

    SHAREPOINT_SITE_URL=http://your-sharepoint-site-url e.g. 'http://portal/sites'
    SHAREPOINT_SITE_PATH=site_path e.g. 'DocuCenter2'
    SHAREPOINT_USERNAME=your_domain\your_sharepoint_username e.g. MYCOMPANY.COM\username
    SHAREPOINT_PASSWORD=your_sharepoint_password
    SHAREPOINT_LIBRARY_NAME=YourDocumentLibrary e.g. 'Benefit Library'
    SHAREPOINT_LIBRARY_NAME_BENEFIT=YourDocumentLibrary e.g. 'Benefit Library'
    SHAREPOINT_LIBRARY_NAME_DMU=YourDocumentLibrary e.g. 'DMU Library'
    DB_TABLE_1=your_table_name
    ```

5. Run the FastAPI application:

    ```sh
    uvicorn main:app --reload
    ```

6. Access the API documentation at `http://127.0.0.1:8000/docs`

## Project Structure

- `app.py`: The main FastAPI application file that handles the endpoints.
- `database.py`: Contains functions for database connection, data retrieval, and status update.
- `fetch_list_item_details.py`: Utility script to fetch SharePoint list item properties and list item type.
- `.env`: Environment variables configuration file (not included in the repository).
- `requirements.txt`: List of required Python packages.

## Endpoints

- **POST /upload_images**: Retrieves images and metadata from SQL Server, uploads the images to SharePoint, and updates the SQL Server database with the new links and statuses.

## Fetching SharePoint List Item Details
A utility script fetch_list_item_details.py is provided to fetch and print SharePoint list item properties and list item type.

1. Run the script:

   ```sh
   python fetch_list_item_details.py
   ```
   This will print the list item type and the properties of the first item in the specified document library

## Database Configuration
Ensure your SQL Server database has the following structure (adjust field names and types as needed):

   ```sql
   CREATE TABLE Documents (
    fileid INT PRIMARY KEY,
    pin NVARCHAR(18),
    firstname NVARCHAR(100),
    lastname NVARCHAR(100),
    middlename NVARCHAR(100),
    phone NVARCHAR(30),
    pin NVARCHAR(18),
    employer_name NVARCHAR(100),
    employer_code NVARCHAR(30),
    description NVARCHAR(128),
    doctype NVARCHAR(10),
    doctype_desc NVARCHAR(100),
    file_item VARBINARY(MAX),
    filename NVARCHAR(255),
    file_link NVARCHAR(300),
    status NVARCHAR(500)
   );
   ```

## Dependencies
The project relies on the following libraries, specified in requirements.txt:

- fastapi
- uvicorn
- pyodbc
- pandas
- requests
- python-dotenv
- Office365-REST-Python-Client
- requests_ntlm
- pillow
- python-magic
- sqlalchemy
- python-magic-bin
- pydantic

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request.

## License
This project is licensed under [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)