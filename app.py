from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import get_document_and_metadata, update_document_status, get_documents_with_file_path
from requests_ntlm import HttpNtlmAuth
from dotenv import load_dotenv
from PIL import Image
import magic
import io
import os
import requests
from datetime import datetime
from urllib.parse import quote, urljoin


class DocTypeRequest(BaseModel):
    document_type: str


# Load environment variables from .env file
load_dotenv()

app = FastAPI()


# SharePoint credentials and site URL
base_site_url = os.getenv('SHAREPOINT_SITE_URL')  # e.g., "http://portal/sites"
site_path = os.getenv('SHAREPOINT_SITE_PATH')    # e.g., "DocuCenter2"
username = os.getenv('SHAREPOINT_USERNAME')
password = os.getenv('SHAREPOINT_PASSWORD')

# Ensure the base site URL is correct
if not base_site_url.endswith('/'):
    base_site_url += '/'

# Full site URL for API requests
site_url = urljoin(base_site_url, f"{site_path}/")

# NTLM authentication
ntlm_auth = HttpNtlmAuth(username, password)


def is_valid_image(file_item):
    try:
        image = Image.open(io.BytesIO(file_item))
        image.verify()
        return True
    except (IOError, SyntaxError):
        return False


def get_mime_type(file_item):
    mime = magic.Magic(mime=True)
    return mime.from_buffer(file_item)


def sanitize_doctype(doctype):
    # Replace or remove special characters that might cause issues
    return doctype.replace("/", "-").replace("\\", "-").replace(" ", "_")


def generate_unique_filename(pin, doctype, original_filename):
    sanitized_doctype = sanitize_doctype(doctype)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    name, ext = os.path.splitext(original_filename)
    unique_name = f"{pin}_{sanitized_doctype}_{timestamp}{ext}"
    return unique_name


def get_request_digest():
    digest_url = urljoin(site_url, '_api/contextinfo')
    digest_headers = {
        "accept": "application/json;odata=verbose",
        "content-type": "application/json;odata=verbose"
    }
    digest_response = requests.post(digest_url, headers=digest_headers, auth=ntlm_auth)
    digest_value = digest_response.json()['d']['GetContextWebInformation']['FormDigestValue']
    return digest_value


def get_list_item_type(sharepoint_library_name):
    list_url = urljoin(site_url, f"_api/web/lists/GetByTitle('{sharepoint_library_name}')")
    headers = {
        "accept": "application/json;odata=verbose"
    }
    response = requests.get(list_url, headers=headers, auth=ntlm_auth)
    if response.status_code == 200:
        list_data = response.json()
        return list_data['d']['ListItemEntityTypeFullName']
    else:
        raise Exception(f"Failed to fetch list item type: {response.status_code}, {response.text}")


@app.post("/upload/documents")
async def upload_access_documents(request: DocTypeRequest):
    document_type = request.document_type.lower()

    if document_type not in ["dmu", "benefit"]:
        raise HTTPException(status_code=400, detail="Invalid document type. Must be 'dmu' or 'benefit'.")

    if document_type == 'dmu':
        library_name = os.getenv('SHAREPOINT_LIBRARY_NAME_DMU')
    else:
        library_name = os.getenv('SHAREPOINT_LIBRARY_NAME_BENEFIT')

    try:
        documents_data = get_document_and_metadata(document_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Fetch the correct List Item Entity Type for the library
    try:
        list_item_type = get_list_item_type(library_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    for _, row in documents_data.iterrows():
        file_id = row['fileid']
        pin = row['pin']
        firstname = row['firstname']
        lastname = row['lastname']
        middlename = row['middlename']
        phone = row['phone']
        employer_name = row['employer_name']
        employer_code = row['employer_code']
        description = row['desc']
        doctype = row['doc_type']
        file_item = row['file_item']
        original_filename = row['filename']

        # Generate a unique filename
        filename = generate_unique_filename(pin, doctype, original_filename)

        # Check the MIME type of the file item
        mime_type = get_mime_type(file_item)

        # Validate file types
        valid_types = [
            'image/jpeg',
            'image/png',
            'image/bmp',
            'image/gif',
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',  # For .xls files
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'  # For .xlsx files
        ]

        # Validate image file types
        if mime_type in ['image/jpeg', 'image/png', 'image/bmp', 'image/gif']:
            if not is_valid_image(file_item):
                update_document_status(file_id, None, "Invalid document file", original_filename)
                continue
        elif mime_type not in valid_types:
            update_document_status(file_id, None, f"Unsupported file type: {mime_type}", original_filename)
            continue

        # Upload the file to SharePoint
        try:
            digest_value = get_request_digest()

            # Construct the folder URL
            encoded_library_name = quote(library_name)
            folder_url = urljoin(site_url, f"_api/web/GetFolderByServerRelativeUrl('/sites/{site_path}/{encoded_library_name}')")

            # Check if the folder exists in SharePoint
            folder_response = requests.get(folder_url, headers={"accept": "application/json;odata=verbose"}, auth=ntlm_auth)

            if folder_response.status_code != 200:
                update_document_status(file_id, None, f"Folder not found: {folder_response.status_code}", original_filename)
                continue

            upload_url = urljoin(site_url, f"_api/web/GetFolderByServerRelativeUrl('/sites/{site_path}/{encoded_library_name}')/Files/add(url='{quote(filename)}',overwrite=true)")
            headers = {
                "accept": "application/json;odata=verbose",
                "content-type": "application/octet-stream",
                "X-RequestDigest": digest_value
            }

            upload_response = requests.post(upload_url, headers=headers, data=file_item, auth=ntlm_auth)

            if upload_response.status_code in [200, 201]:  # Check for successful status codes
                # Get the uploaded file item
                file_url = f"/sites/{site_path}/{encoded_library_name}/{quote(filename)}"
                file_item_url = urljoin(site_url, f"_api/web/GetFileByServerRelativeUrl('{file_url}')/ListItemAllFields")

                file_item_response = requests.get(file_item_url, auth=ntlm_auth, headers={"accept": "application/json;odata=verbose"})

                if file_item_response.status_code == 200:
                    file_item_json = file_item_response.json()
                    item_id = file_item_json['d']['ID']
                    update_metadata_url = urljoin(site_url, f"_api/web/lists/getbytitle('{encoded_library_name}')/items({item_id})")
                    update_data = {
                        "__metadata": {"type": list_item_type},  # Use the correct list item type
                        "RSAPin": pin,
                        "FirstName": firstname,
                        "Surname": lastname,
                        "OtherNames": middlename,
                        "MobileNo": phone,
                        "EmployerName": employer_name,
                        "EmployerCode": employer_code,
                        "DocumentType": doctype
                    }
                    update_headers = {
                        "accept": "application/json;odata=verbose",
                        "content-type": "application/json;odata=verbose",
                        "X-HTTP-Method": "MERGE",
                        "If-Match": "*",
                        "X-RequestDigest": digest_value  # Include the request digest in headers
                    }
                    update_response = requests.post(update_metadata_url, headers=update_headers, json=update_data, auth=ntlm_auth)
                    if update_response.status_code in [200, 204]:  # 204 is No Content, which is also a success status
                        # Construct the SharePoint file link
                        sharepoint_file_link = urljoin(site_url, f"/sites/{site_path}/{encoded_library_name}/{quote(filename)}")

                        # Update the SQL Server database with the SharePoint file link and status
                        update_document_status(file_id, sharepoint_file_link, "Uploaded successfully", original_filename)
                    else:
                        update_document_status(file_id, None, f"Failed to update metadata: {update_response.text}", original_filename)
                else:
                    update_document_status(file_id, None, f"Failed to get file item: {file_item_response.text}", original_filename)
            else:
                update_document_status(file_id, None, f"Failed to upload: {upload_response.text}", original_filename)
        except Exception as e:
            update_document_status(file_id, None, f"Failed to upload: {str(e)}", original_filename)

    return {"status": "success", "message": "Files uploaded successfully"}


@app.post("/upload/documents-from-path")
async def upload_documents_from_path(request: DocTypeRequest):
    document_type = request.document_type.lower()

    if document_type not in ["dmu", "benefit"]:
        raise HTTPException(status_code=400, detail="Invalid document type. Must be 'dmu' or 'benefit'.")

    if document_type == 'dmu':
        library_name = os.getenv('SHAREPOINT_LIBRARY_NAME_DMU')
    else:
        library_name = os.getenv('SHAREPOINT_LIBRARY_NAME_BENEFIT')

    try:
        documents_data = get_documents_with_file_path(document_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Fetch the correct List Item Entity Type for the library
    try:
        list_item_type = get_list_item_type(library_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    for _, row in documents_data.iterrows():
        file_id = row['fileid']
        pin = row['pin']
        firstname = row['firstname']
        lastname = row['lastname']
        middlename = row['middlename']
        phone = row['phone']
        employer_name = row['employer_name']
        employer_code = row['employer_code']
        description = row['desc']
        doctype = row['doc_type']
        file_path = row['file_path']
        original_filename = os.path.basename(file_path)

        # Generate a unique filename
        filename = generate_unique_filename(pin, doctype, original_filename)

        # Check if the file exists
        if not os.path.exists(file_path):
            update_document_status(file_id, None, "File not found", original_filename)
            continue

        # Check the file extension and validate file types
        ext = os.path.splitext(original_filename)[1].lower()
        valid_types = [
            '.jpeg', '.jpg', '.png', '.bmp', '.gif', '.pdf', '.doc', '.docx', '.xls', '.xlsx'
        ]

        if ext not in valid_types:
            update_document_status(file_id, None, f"Unsupported file type: {ext}", original_filename)
            continue

        # Upload the file to SharePoint
        try:
            # Read the file content from the file path
            with open(file_path, 'rb') as file:
                file_content = file.read()

            digest_value = get_request_digest()

            # Construct the folder URL
            encoded_library_name = quote(library_name)
            folder_url = urljoin(site_url,
                                 f"_api/web/GetFolderByServerRelativeUrl('/sites/{site_path}/{encoded_library_name}')")

            # Check if the folder exists in SharePoint
            folder_response = requests.get(folder_url,
                                           headers={"accept": "application/json;odata=verbose"}, auth=ntlm_auth)

            if folder_response.status_code != 200:
                update_document_status(file_id, None,
                                       f"Folder not found: {folder_response.status_code}", original_filename)
                continue

            upload_url = urljoin(site_url,
                                 f"_api/web/GetFolderByServerRelativeUrl('/sites/{site_path}/{encoded_library_name}')/Files/add(url='{quote(filename)}',overwrite=true)")
            headers = {
                "accept": "application/json;odata=verbose",
                "content-type": "application/octet-stream",
                "X-RequestDigest": digest_value
            }

            upload_response = requests.post(upload_url, headers=headers, data=file_content, auth=ntlm_auth)

            if upload_response.status_code in [200, 201]:  # Check for successful status codes
                # Get the uploaded file item
                file_url = f"/sites/{site_path}/{encoded_library_name}/{quote(filename)}"
                file_item_url = urljoin(site_url, f"_api/web/GetFileByServerRelativeUrl('{file_url}')/ListItemAllFields")

                file_item_response = requests.get(file_item_url, auth=ntlm_auth,
                                                  headers={"accept": "application/json;odata=verbose"})

                if file_item_response.status_code == 200:
                    file_item_json = file_item_response.json()
                    item_id = file_item_json['d']['ID']
                    update_metadata_url = urljoin(site_url, f"_api/web/lists/getbytitle('{encoded_library_name}')/items({item_id})")
                    update_data = {
                        "__metadata": {"type": list_item_type},  # Use the correct list item type
                        "RSAPin": pin,
                        "FirstName": firstname,
                        "Surname": lastname,
                        "OtherNames": middlename,
                        "MobileNo": phone,
                        "EmployerName": employer_name,
                        "EmployerCode": employer_code,
                        "DocumentType": doctype
                    }
                    update_headers = {
                        "accept": "application/json;odata=verbose",
                        "content-type": "application/json;odata=verbose",
                        "X-HTTP-Method": "MERGE",
                        "If-Match": "*",
                        "X-RequestDigest": digest_value  # Include the request digest in headers
                    }
                    update_response = requests.post(update_metadata_url, headers=update_headers, json=update_data, auth=ntlm_auth)
                    if update_response.status_code in [200, 204]:  # 204 is No Content, which is also a success status
                        # Construct the SharePoint file link
                        sharepoint_file_link = urljoin(site_url, f"/sites/{site_path}/{encoded_library_name}/{quote(filename)}")

                        # Update the SQL Server database with the SharePoint file link and status
                        update_document_status(file_id, sharepoint_file_link, "Uploaded successfully", original_filename)
                    else:
                        update_document_status(file_id, None, f"Failed to update metadata: {update_response.text}", original_filename)
                else:
                    update_document_status(file_id, None, f"Failed to get file item: {file_item_response.text}", original_filename)
            else:
                update_document_status(file_id, None, f"Failed to upload: {upload_response.text}", original_filename)
        except Exception as e:
            update_document_status(file_id, None, f"Failed to upload: {str(e)}", original_filename)

    return {"status": "success", "message": "Files uploaded successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
