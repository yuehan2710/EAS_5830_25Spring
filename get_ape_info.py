from web3 import Web3
from web3.providers.rpc import HTTPProvider
import requests
import json

bayc_address = "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D"
contract_address = Web3.to_checksum_address(bayc_address)

# You will need the ABI to connect to the contract
# The file 'abi.json' has the ABI for the bored ape contract
# In general, you can get contract ABIs from etherscan
# https://api.etherscan.io/api?module=contract&action=getabi&address=0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D
with open('ape_abi.json', 'r') as f:
  abi = json.load(f)

############################
# Connect to an Ethereum node
api_url = "https://mainnet.infura.io/v3/e07478f88d89454baa06972032a6dcc2"  # YOU WILL NEED TO PROVIDE THE URL OF AN ETHEREUM NODE
provider = HTTPProvider(api_url)
web3 = Web3(provider)

# Create contract object
contract = web3.eth.contract(address=contract_address, abi=abi)

def get_ape_info(ape_id):
  assert isinstance(ape_id, int), f"{ape_id} is not an int"
  assert 0 <= ape_id, f"{ape_id} must be at least 0"
  assert 9999 >= ape_id, f"{ape_id} must be less than 10,000"

  data = {'owner': "", 'image': "", 'eyes': ""}

  # YOUR CODE HERE

  #assert isinstance(data, dict), f'get_ape_info{ape_id} should return a dict'
  #assert all([a in data.keys() for a in
              #['owner', 'image', 'eyes']]), f"return value should include the keys 'owner','image' and 'eyes'"

  try:
    # Get the owner of the Ape NFT
    data['owner'] = contract.functions.ownerOf(ape_id).call()
    
    # Get the tokenURI and fetch metadata from IPFS
    token_uri = contract.functions.tokenURI(ape_id).call()
    ipfs_hash = token_uri.replace("ipfs://", "")
    ipfs_url = f"https://ipfs.io/ipfs/{ipfs_hash}"
    response = requests.get(ipfs_url)
    
    if response.status_code == 200:
      metadata = response.json()
      data['image'] = metadata.get('image', '')
      
      # Find the 'eyes' attribute
      attributes = metadata.get('attributes', [])
      for attr in attributes:
        if attr.get('trait_type') == 'Eyes':
          data['eyes'] = attr.get('value', '')
          break
    else:
      print(f"Failed to fetch metadata: {response.status_code}")
  
  except Exception as e:
    print(f"Error retrieving Ape info: {e}")
  
  return data
