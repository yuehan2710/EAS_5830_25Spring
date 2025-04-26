from web3 import Web3
from web3.providers.rpc import HTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware #Necessary for POA chains
from datetime import datetime
import json
import pandas as pd

import os
import json
import time
from eth_account import Account
from eth_account.signers.local import LocalAccount
from dotenv import load_dotenv # Optional: for managing API keys if needed

# --- Configuration ---
CONTRACT_INFO_FILE = "contract_info.json"
SECRET_KEY_FILE = "secret_key.txt"
SCAN_BLOCK_RANGE = 5 # Number of recent blocks to scan


# --- Helper Functions ---
def connect_to(chain):
    if chain == 'source':  # The source contract chain is avax
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc" #AVAX C-chain testnet

    if chain == 'destination':  # The destination contract chain is bsc
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/" #BSC testnet

    if chain in ['source','destination']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3


def get_contract_info(chain, contract_info):
    """
        Load the contract_info file into a dictionary
        This function is used by the autograder and will likely be useful to you
    """
    try:
        with open(contract_info, 'r')  as f:
            contracts = json.load(f)
    except Exception as e:
        print( f"Failed to read contract info\nPlease contact your instructor\n{e}" )
        return 0
    return contracts[chain]


def load_warden_account(secret_key_file):
    """Loads the warden's private key and creates an Account object."""
    try:
        with open(secret_key_file, "r") as f:
            key = f.readline().strip()
        if not key:
            raise ValueError(f"Secret key file '{secret_key_file}' is empty.")
        account: LocalAccount = Account.from_key(key)
        print(f"Loaded Warden Account: {account.address}")
        return account
    except FileNotFoundError:
        print(f"Error: {secret_key_file} not found.")
        raise
    except Exception as e:
        print(f"Failed to load warden account: {e}")
        raise

def send_transaction(w3: Web3, account: LocalAccount, tx_params: dict):
    """Signs and sends a transaction, waiting for the receipt."""
    try:
        # Estimate gas if not provided
        if 'gas' not in tx_params:
             tx_params['gas'] = w3.eth.estimate_gas(tx_params)
             print(f"Estimated gas: {tx_params['gas']}")

        # Set gas price if not provided (using current gas price)
        if 'gasPrice' not in tx_params:
            tx_params['gasPrice'] = w3.eth.gas_price
            print(f"Using gas price: {tx_params['gasPrice']}")

        # Get nonce
        tx_params['nonce'] = w3.eth.get_transaction_count(account.address)
        print(f"Using nonce: {tx_params['nonce']}")


        signed_tx = w3.eth.account.sign_transaction(tx_params, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"Transaction sent with hash: {tx_hash.hex()}")

        # Wait for transaction receipt
        print("Waiting for transaction receipt...")
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180) # Wait up to 3 minutes
        print(f"Transaction confirmed in block: {tx_receipt.blockNumber}")
        if tx_receipt.status == 0:
            print("Warning: Transaction failed (reverted).")
            # Consider raising an error here or implementing retry logic
        return tx_receipt
    except ValueError as ve:
        # Often indicates issues like insufficient funds or gas estimation problems
        print(f"Transaction Value Error: {ve}")
        # Check if the error message contains useful info (e.g., from a require statement)
        if 'message' in str(ve):
             print(f"Error message: {ve}")
        raise
    except Exception as e:
        print(f"Error sending transaction: {e}")
        raise

# --- Event Handling Functions ---

def handle_deposit_event(event, warden_account, contracts_info):
    """Handles a Deposit event found on the source chain by calling wrap() on the destination."""
    print("-" * 20)
    print(f"Handling Deposit Event from Source (AVAX)...")
    print(f"  Token: {event.args.token}")
    print(f"  Recipient: {event.args.recipient}")
    print(f"  Amount: {event.args.amount}")
    print(f"  Tx Hash: {event.transactionHash.hex()}")

    try:
        w3_dest = connect_to('destination')
        dest_info = contracts_info['destination']
        dest_contract = w3_dest.eth.contract(address=dest_info['address'], abi=dest_info['abi'])

        # Prepare the wrap() transaction
        wrap_tx = dest_contract.functions.wrap(
            event.args.token,      # _underlying_token (address on source chain)
            event.args.recipient,  # _recipient (final recipient address)
            event.args.amount      # _amount
        ).build_transaction({
            'from': warden_account.address,
            'chainId': w3_dest.eth.chain_id,
            # Gas and Nonce will be handled by send_transaction
        })

        print(f"Sending wrap transaction to Destination (BSC) contract: {dest_info['address']}")
        send_transaction(w3_dest, warden_account, wrap_tx)
        print("wrap() transaction successful.")

    except Exception as e:
        print(f"Error handling Deposit event and calling wrap(): {e}")
    print("-" * 20)


def handle_unwrap_event(event, warden_account, contracts_info):
    """Handles an Unwrap event found on the destination chain by calling withdraw() on the source."""
    print("-" * 20)
    print(f"Handling Unwrap Event from Destination (BSC)...")
    print(f"  Underlying Token: {event.args.underlying_token}")
    print(f"  Wrapped Token: {event.args.wrapped_token}")
    print(f"  From (Burner): {event.args.frm}")
    print(f"  To (Recipient): {event.args.to}") # This is the recipient on the source chain
    print(f"  Amount: {event.args.amount}")
    print(f"  Tx Hash: {event.transactionHash.hex()}")

    try:
        w3_source = connect_to('source')
        source_info = contracts_info['source']
        source_contract = w3_source.eth.contract(address=source_info['address'], abi=source_info['abi'])

        # Prepare the withdraw() transaction
        withdraw_tx = source_contract.functions.withdraw(
            event.args.underlying_token, # _token (address on source chain)
            event.args.to,               # _recipient (final recipient address on source chain)
            event.args.amount            # _amount
        ).build_transaction({
            'from': warden_account.address,
            'chainId': w3_source.eth.chain_id,
            # Gas and Nonce will be handled by send_transaction
        })

        print(f"Sending withdraw transaction to Source (AVAX) contract: {source_info['address']}")
        send_transaction(w3_source, warden_account, withdraw_tx)
        print("withdraw() transaction successful.")

    except Exception as e:
        print(f"Error handling Unwrap event and calling withdraw(): {e}")
    print("-" * 20)




# --- Main Scanning Function ---    
def scan_blocks(chain, contracts_info, warden_account):
    """
        chain - (string) should be either "source" or "destination"
        Scan the last 5 blocks of the source and destination chains
        Look for 'Deposit' events on the source chain and 'Unwrap' events on the destination chain
        When Deposit events are found on the source chain, call the 'wrap' function the destination chain
        When Unwrap events are found on the destination chain, call the 'withdraw' function on the source chain
    """

    # This is different from Bridge IV where chain was "avax" or "bsc"
    if chain not in ['source','destination']:
        print( f"Invalid chain: {chain}" )
        return 0
    
        #YOUR CODE HERE
    
    print(f"\n=== Scanning {chain.upper()} Chain ===")
    try:
        w3 = connect_to(chain)
        chain_info = contracts_info[chain]
        contract_address = chain_info['address']
        contract_abi = chain_info['abi']
        contract = w3.eth.contract(address=contract_address, abi=contract_abi)

        # Determine block range to scan
        latest_block = w3.eth.get_block_number()
        start_block = max(0, latest_block - SCAN_BLOCK_RANGE + 1) # Ensure start_block is not negative
        end_block = latest_block

        print(f"Scanning blocks {start_block} to {end_block} on {chain} for contract {contract_address}")

        if chain == 'source':
            # Listen for 'Deposit' events on the Source contract
            try:
                event_filter = contract.events.Deposit.create_filter(
                    fromBlock=start_block,
                    toBlock=end_block
                )
                events = event_filter.get_all_entries()
                print(f"Found {len(events)} Deposit event(s).")
                for event in events:
                    # Process each Deposit event
                    handle_deposit_event(event, warden_account, contracts_info)
            except Exception as e:
                 # Might happen if the event isn't defined correctly in the ABI
                print(f"Error creating/fetching Deposit event filter on {chain}: {e}")


        elif chain == 'destination':
            # Listen for 'Unwrap' events on the Destination contract
            try:
                event_filter = contract.events.Unwrap.create_filter(
                    fromBlock=start_block,
                    toBlock=end_block
                )
                events = event_filter.get_all_entries()
                print(f"Found {len(events)} Unwrap event(s).")
                for event in events:
                    # Process each Unwrap event
                    handle_unwrap_event(event, warden_account, contracts_info)
            except Exception as e:
                # Might happen if the event isn't defined correctly in the ABI
                print(f"Error creating/fetching Unwrap event filter on {chain}: {e}")

    except ConnectionError as e:
        print(f"Connection error while scanning {chain}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while scanning {chain}: {e}")


# --- Main Execution ---

if __name__ == "__main__":
    print("Starting Bridge Listener Script...")
    print(f"Current time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 1. Load configuration
        all_contract_info = get_contract_info(CONTRACT_INFO_FILE)
        warden = load_warden_account(SECRET_KEY_FILE)

        # Check if warden address matches the one in the config file
        if warden.address != all_contract_info['warden_address']:
             print(f"Warning: Loaded warden address {warden.address} does not match address in {CONTRACT_INFO_FILE} ({all_contract_info['warden_address']})")


        # 2. Scan Source Chain (AVAX) for Deposits
        scan_blocks('source', all_contract_info, warden)

        # 3. Scan Destination Chain (BSC) for Unwraps
        scan_blocks('destination', all_contract_info, warden)

        print("\nBridge Listener Script Finished.")

    except (FileNotFoundError, ValueError, ConnectionError) as e:
        print(f"\nInitialization Error: Could not start bridge script. {e}")
    except Exception as e:
        print(f"\nAn unexpected critical error occurred: {e}")
