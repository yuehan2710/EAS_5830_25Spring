import requests
import json

def pin_to_ipfs(data):
	assert isinstance(data,dict), f"Error pin_to_ipfs expects a dictionary"
	# Convert dictionary to JSON bytes
	json_data = json.dumps(data).encode('utf-8')

	# Send data to IPFS node
	files = {'file': json_data}
	response = requests.post(f"{IPFS_API_URL}/add", files=files)

	if response.status_code == 200:
		cid = response.json()['Hash']  # Extract CID
		return cid
  else:
		raise Exception(f"Error: Failed to store data on IPFS: {response.text}")

def get_from_ipfs(cid,content_type="json"):
	assert isinstance(cid,str), f"get_from_ipfs accepts a cid in the form of a string"
	# Fetch data from IPFS
  response = requests.get(f"https://ipfs.io/ipfs/{cid}")  # Using public IPFS gateway

	if response.status_code == 200:
			data = response.json()  # Parse JSON response
			assert isinstance(data, dict), f"get_from_ipfs should return a dict"
			return data
	else:
			raise Exception(f"Error: Failed to retrieve data from IPFS: {response.text}")

