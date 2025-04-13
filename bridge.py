from web3 import Web3
from web3.providers.rpc import HTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware #Necessary for POA chains
from datetime import datetime
import json
import pandas as pd


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



def scan_blocks(chain, contract_info="contract_info.json"):
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

    # Connect to blockchain
    w3 = connect_to(chain)
    other_chain = 'destination' if chain == 'source' else 'source'
    other_w3 = connect_to(other_chain)

    # Load contract ABIs and addresses
    contracts = get_contract_info(contract_info=contract_info)
    contract_address = contracts[chain]['address']
    abi = contracts[chain]['abi']
    other_contract_address = contracts[other_chain]['address']
    other_abi = contracts[other_chain]['abi']

    contract = w3.eth.contract(address=contract_address, abi=abi)
    other_contract = other_w3.eth.contract(address=other_contract_address, abi=other_abi)

    # Load warden credentials
    warden_private_key = contracts['warden']['private_key']
    warden_address = contracts['warden']['address']

    # Get latest block number
    latest_block = w3.eth.block_number

    # Check past 5 blocks
    for block_number in range(latest_block - 5, latest_block + 1):
        block = w3.eth.get_block(block_number, full_transactions=True)

        for tx in block.transactions:
            receipt = w3.eth.get_transaction_receipt(tx['hash'])
            logs = contract.events.Deposit().process_receipt(receipt) if chain == 'source' else \
                   contract.events.Unwrap().process_receipt(receipt)

            for event in logs:
                args = event['args']

                if chain == 'source':
                    # Call wrap on destination
                    tx = other_contract.functions.wrap(
                        args['from'], args['to'], args['amount'],
                        args['nonce'], args['symbol'],
                        args['sourceToken']
                    ).build_transaction({
                        'chainId': other_w3.eth.chain_id,
                        'gas': 500000,
                        'gasPrice': other_w3.eth.gas_price,
                        'nonce': other_w3.eth.get_transaction_count(warden_address),
                    })

                else:
                    # Call withdraw on source
                    tx = other_contract.functions.withdraw(
                        args['from'], args['to'], args['amount'],
                        args['nonce'], args['symbol'],
                        args['destinationToken']
                    ).build_transaction({
                        'chainId': other_w3.eth.chain_id,
                        'gas': 500000,
                        'gasPrice': other_w3.eth.gas_price,
                        'nonce': other_w3.eth.get_transaction_count(warden_address),
                    })

                signed_tx = other_w3.eth.account.sign_transaction(tx, private_key=warden_private_key)
                tx_hash = other_w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                print(f"✅ Relayed transaction: {tx_hash.hex()}")

