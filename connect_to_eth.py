import json
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from web3.providers.rpc import HTTPProvider

'''
If you use one of the suggested infrastructure providers, the url will be of the form
now_url  = f"https://eth.nownodes.io/{now_token}"
alchemy_url = f"https://eth-mainnet.alchemyapi.io/v2/{alchemy_token}"
infura_url = f"https://mainnet.infura.io/v3/{infura_token}"
'''

def connect_to_eth():
	url = "https://bsc-testnet-rpc.publicnode.com"  # FILL THIS IN
	w3 = Web3(HTTPProvider(url))
	assert w3.is_connected(), f"Failed to connect to provider at {url}"
	return w3


def connect_with_middleware(contract_json):
	""" ✅ Connect to Binance Smart Chain (BSC) Testnet with middleware """
	bsc_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"  # ✅ BSC Testnet RPC

	w3 = Web3(HTTPProvider(bsc_url))

	# ✅ Ensure Web3 is connected before injecting middleware
	if not w3.is_connected():
			raise ConnectionError(f"❌ Failed to connect to BSC provider at {bsc_url}")
	print("✅ Successfully connected to Binance Smart Chain!")

	# ✅ Inject PoA middleware
	w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

	# ✅ Re-check Web3 connection after middleware
	if not w3.is_connected():
			raise ConnectionError("❌ Web3 instance lost connection after middleware injection.")
	print("✅ Web3 instance is still connected after middleware!")

	# ✅ Fetch the latest block number
	try:
			block_number = w3.eth.block_number
			print(f"✅ Successfully retrieved block {block_number}")
	except Exception as e:
			raise ConnectionError(f"❌ Error fetching block number: {e}")

	# ✅ Load contract details
	with open(contract_json, "r") as f:
			data = json.load(f)
			data = data['bsc']  # Assuming contract is under "bsc" key
			address = data['address']
			abi = data['abi']

	# ✅ Create contract object
	contract = w3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)
	print(f"✅ Connected to contract at {contract.address}")

	return w3, contract


if __name__ == "__main__":
	connect_to_eth()
