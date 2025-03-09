import requests
import json

# Infura IPFS API URL
IPFS_API_URL = "https://ipfs.infura.io:5001/api/v0"

# Replace these with your Infura credentials
INFURA_PROJECT_ID = "your_project_id"
INFURA_PROJECT_SECRET = "your_project_secret"

# Authentication for Infura
AUTH = (INFURA_PROJECT_ID, INFURA_PROJECT_SECRET)

def pin_to_ipfs(data):
	"""Store a dictionary as JSON on IPFS using Infura and return its CID."""
	assert isinstance(data,dict), f"Error pin_to_ipfs expects a dictionary"

	json_data = json.dumps(data).encode("utf-8")
	files = {"file": json_data}

	# Send data to Infura IPFS with authentication
	response = requests.post(f"{IPFS_API_URL}/add", files=files, auth=AUTH)

	if response.status_code == 200:
			cid = response.json()["Hash"]
			return cid
	else:
			raise Exception(f"Error: Failed to store data on IPFS: {response.text}")
			

def get_from_ipfs(cid,content_type="json"):
	"""Retrieve JSON data from IPFS using Infura."""
	assert isinstance(cid,str), f"get_from_ipfs accepts a cid in the form of a string"

	# Use a public IPFS gateway for fetching data
	response = requests.get(f"https://{IPFS_API_URL}/ipfs/{cid}")

	if response.status_code == 200:
			data = response.json()
			assert isinstance(data, dict), "get_from_ipfs should return a dict"
			return data
	else:
			raise Exception(f"Error: Failed to retrieve data from IPFS: {response.text}")


