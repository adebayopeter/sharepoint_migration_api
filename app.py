from fastapi import FastAPI, HTTPException
from database import get_images_and_metadata, update_image_status
import requests
from requests_ntlm import HttpNtlmAuth
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.authentication_context import AuthenticationContext
from dotenv import load_dotenv
from PIL import Image
import magic
import io
import os

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# SharePoint credentials and site URL
site_url = os.getenv('SHAREPOINT_SITE_URL')
username = os.getenv('SHAREPOINT_USERNAME')
password = os.getenv('SHAREPOINT_PASSWORD')
library_name = os.getenv('SHAREPOINT_LIBRARY_NAME')


def is_valid_image(file_item):
    try:
        image = Image.open(io.BytesIO(file_item))
        image.verify()
        return True
    except (IOError, SyntaxError) as e:
        return False


def get_mime_type(file_item):
    mime = magic.Magic(mime=True)
    return mime.from_buffer(file_item)


@app.post("/upload_images")
async def upload_images():
    try:
        images_data = get_images_and_metadata()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # NTLM authentication context
    auth_context = AuthenticationContext(site_url)
    auth_context.acquire_token_for_user(username, password)
    ctx = ClientContext(site_url, auth_context)

    for _, row in images_data.iterrows():
        file_id = row['fileid']
        pin = row['pin']
        description = row['desc']
        doctype = row['doctype']
        doctype_desc = row['doctype_desc']
        file_item = row['file_item']
        filename = row['filename']

        # Check the MIME type of the file item
        mime_type = get_mime_type(file_item)

        # Validate file types
        valid_types = [
            'image/jpeg', 'image/png', 'image/bmp', 'application/pdf',
            'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]

        # Validate image file types
        if mime_type in ['image/jpeg', 'image/png', 'image/bmp']:
            if not is_valid_image(file_item):
                update_image_status(file_id, None, "Invalid document file", filename)
                continue
        elif mime_type not in valid_types:
            update_image_status(file_id, None, f"Unsupported file type: {mime_type}", filename)
            continue

        # Upload the image to SharePoint
        try:
            target_folder = ctx.web.lists.get_by_title(library_name).root_folder
            upload_file = target_folder.upload_file(filename, file_item).execute_query()

            # Update file metadata
            file_item = upload_file.listItemAllFields
            file_item.set_property('PIN', pin)
            file_item.set_property('Document Type', doctype_desc)
            file_item.update()
            ctx.execute_query()

            # Construct the SharePoint image link
            sharepoint_image_link = f"{site_url}/{library_name}/{filename}"

            # Update the SQL Server database with the SharePoint image link and status
            update_image_status(file_id, sharepoint_image_link, "Uploaded successfully", filename)
        except Exception as e:
            update_image_status(file_id, None, f"Failed to upload {str(e)}", filename)

    return {"status": "success", "message": "Images uploaded successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
