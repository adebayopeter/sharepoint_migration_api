from fastapi import FastAPI, HTTPException
from database import get_images_and_metadata, update_image_status
import requests
from requests_ntlm import HttpNtlmAuth
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.authentication_context import AuthenticationContext
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# SharePoint credentials and site URL
site_url = os.getenv('SHAREPOINT_SITE_URL')
username = os.getenv('SHAREPOINT_USERNAME')
password = os.getenv('SHAREPOINT_PASSWORD')
library_name = os.getenv('SHAREPOINT_LIBRARY_NAME')


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
        image_id = row['id']
        image_url = row['image_url']
        filename = row['filename']
        metadata = {
            "filename": filename,
            "metadata_field1": row['metadata_field1'],
            "metadata_field2": row['metadata_field2']
        }

        # Download the image
        image_response = requests.get(image_url)
        if image_response.status_code != 200:
            update_image_status(image_id, None, "Failed to download", filename)
            continue
        image_content = image_response.content

        # Upload the image to SharePoint
        try:
            target_folder = ctx.web.lists.get_by_title(library_name).root_folder
            upload_file = target_folder.upload_file(filename, image_content).execute_query()

            # Construct the SharePoint image link
            sharepoint_image_link = f"{site_url}/{library_name}/{metadata['filename']}"

            # Update the SQL Server database with the SharePoint image link and status
            update_image_status(image_id, sharepoint_image_link, "Uploaded successfully", filename)
        except Exception as e:
            update_image_status(image_id, None, f"Failed to upload {str(e)}", filename)

    return {"status": "success", "message": "Images uploaded successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
