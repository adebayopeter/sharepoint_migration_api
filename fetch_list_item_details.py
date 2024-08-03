import requests
from requests_ntlm import HttpNtlmAuth
from dotenv import load_dotenv
import os
from urllib.parse import urljoin

# Load environment variables from .env file
load_dotenv()

# SharePoint credentials and site URL
base_site_url = os.getenv('SHAREPOINT_SITE_URL')  # e.g., "http://portal/sites"
site_path = os.getenv('SHAREPOINT_SITE_PATH')    # e.g., "DocuCenter2"
library_name = os.getenv('SHAREPOINT_LIBRARY_NAME')
username = os.getenv('SHAREPOINT_USERNAME')
password = os.getenv('SHAREPOINT_PASSWORD')

# Ensure the base site URL is correct
if not base_site_url.endswith('/'):
    base_site_url += '/'

# Full site URL for API requests
site_url = urljoin(base_site_url, f"{site_path}/")

# NTLM authentication
ntlm_auth = HttpNtlmAuth(username, password)


# Fetch the List Item Type
def fetch_list_item_type():
    list_url = urljoin(site_url, f"_api/web/lists/GetByTitle('{library_name}')")
    headers = {
        "accept": "application/json;odata=verbose"
    }

    response = requests.get(list_url, headers=headers, auth=ntlm_auth)
    if response.status_code == 200:
        list_data = response.json()
        list_item_type = list_data['d']['ListItemEntityTypeFullName']
        print(f"List Item Type: {list_item_type}")
    else:
        print(f"Failed to fetch list item type: {response.status_code}")
        print(f"Response: {response.text}")


# Fetch List Item Properties
def fetch_list_item_properties():
    list_url = urljoin(site_url, f"_api/web/lists/GetByTitle('{library_name}')/items")
    headers = {
        "accept": "application/json;odata=verbose"
    }
    response = requests.get(list_url, headers=headers, auth=ntlm_auth)
    if response.status_code == 200:
        list_items = response.json()['d']['results']
        if list_items:
            item = list_items[0]  # Fetch properties of the first item
            print("Property Names:")
            for key in item.keys():
                print(key)
        else:
            print("No items found in the library.")
    else:
        print(f"Failed to fetch list items: {response.status_code}")
        print(f"Response: {response.text}")


# Run the function to fetch the List Item Type
fetch_list_item_type()
# Run the function to fetch and print property names
fetch_list_item_properties()
