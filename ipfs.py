import requests
import json

# Pinata API Base URL
PINATA_API_URL = "https://api.pinata.cloud"

# Replace these with your Pinata credentials
PINATA_API_KEY = "99d34519a470d4a1455a"
PINATA_SECRET_API_KEY = "e7b6f2e0f1dacc23fb86155f1d9e60c7b8956b3b38b34eae36365857a805ca98"

# Headers for Pinata authentication
HEADERS = {
	"Content-Type": "application/json",
  "pinata_api_key": PINATA_API_KEY,
  "pinata_secret_api_key": PINATA_SECRET_API_KEY
}

def pin_to_ipfs(data):
	"""Store a dictionary as JSON on IPFS using Pinata and return its CID."""
	assert isinstance(data, dict), "Error: pin_to_ipfs expects a dictionary"

	json_payload = json.dumps({"pinataContent": data})

	response = requests.post(f"{PINATA_API_URL}/pinning/pinJSONToIPFS", 
	                        headers=HEADERS, 
				                  data=json_payload)

	if response.status_code == 200:
		cid = response.json()["IpfsHash"]
		return cid
	else:
		raise Exception(f"Error: Failed to store data on IPFS: {response.text}")
			

def get_from_ipfs(cid,content_type="json"):
	"""Retrieve JSON data from IPFS using a public gateway."""
	assert isinstance(cid, str), "get_from_ipfs expects a CID as a string"

	response = requests.get(f"https://gateway.pinata.cloud/ipfs/{cid}")

	if response.status_code == 200:
		data = response.json()
		assert isinstance(data, dict), "get_from_ipfs should return a dict"
		return data
	else:
		raise Exception(f"Error: Failed to retrieve data from IPFS: {response.text}")



