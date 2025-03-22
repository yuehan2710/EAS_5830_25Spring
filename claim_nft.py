import json
import random
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account

# === Web3 setup for Avalanche Fuji ===
w3 = Web3(Web3.HTTPProvider("https://api.avax-test.network/ext/bc/C/rpc"))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# === Replace with your faucet wallet private key ===
PRIVATE_KEY = "0x59de36ffcf84a15815fae4392a49d7bc7992d101882301f1f8db7860eeff81f3"
account = Account.from_key(PRIVATE_KEY)
ADDRESS = account.address
print(f"Using address: {ADDRESS}")

# === Load ABI from file ===
with open("NFT.abi", "r") as f:
    abi = json.load(f)

contract_address = Web3.to_checksum_address("0x85ac2e065d4526FBeE6a2253389669a12318A412")
contract = w3.eth.contract(address=contract_address, abi=abi)

# === Optional: maxId from contract ===
try:
    max_id = contract.functions.maxId().call()
except:
    max_id = 2**64  # default fallback
print(f"maxId = {max_id}")

# === Generate a random nonce and try to mint ===
def keccak256(input_bytes):
    return int.from_bytes(Web3.keccak(input_bytes), 'big')

for attempt in range(1000):
    nonce = random.getrandbits(256).to_bytes(32, 'big')
    token_id = keccak256(nonce) % max_id

    print(f"[Attempt {attempt}] Trying tokenId = {token_id}")

    try:
        tx = contract.functions.claim(ADDRESS, nonce).build_transaction({
            'from': ADDRESS,
            'nonce': w3.eth.get_transaction_count(ADDRESS),
            'gas': 250000,
            'gasPrice': w3.eth.gas_price,
        })
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        print(f"✅ SUCCESS: Minted tokenId={token_id}")
        print(f"🔗 View: https://testnet.snowtrace.io/tx/{tx_hash.hex()}")
        break  # Stop after first success

    except Exception as e:
        print(f"❌ Reverted: {e}")
