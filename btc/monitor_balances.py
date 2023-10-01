import bdkpython as bdk
import meshtastic.serial_interface
import pandas as pd
import time
import sys
import json
import os

args = sys.argv


def get_blockchain_config():
    return bdk.BlockchainConfig.ELECTRUM(
        bdk.ElectrumConfig(
            "ssl://electrum.blockstream.info:60002",
            None,
            5,
            None,
            100,
            True,
        )
    )

descriptor = bdk.Descriptor("wpkh(tprv8ZgxMBicQKsPcx5nBGsR63Pe8KnRUqmbJNENAfGftF3yuXoMMoVJJcYeUw5eVkm9WBPjWYt6HMWYJNesB5HaNVBaFc1M6dRjWSYnmewUMYy/84h/0h/0h/0/*)", bdk.Network.TESTNET) 
db_config = bdk.DatabaseConfig.MEMORY()
blockchain_config = get_blockchain_config()
blockchain = bdk.Blockchain(blockchain_config)

def name_to_wallet_json(name):
    if not os.path.exists('./wallets/' + name + '.json'):
        print("Wallet does not exist, first create it with new_wallet.py")
        sys.exit()
    f = open('./wallets/' + name + '.json', "r")
    return json.loads(f.read())

def wallet_from_file(wallet_json):
    wallet = bdk.Wallet(
        descriptor=bdk.Descriptor(wallet_json['descriptor'], bdk.Network.TESTNET),
        change_descriptor=bdk.Descriptor(wallet_json['change_descriptor'], bdk.Network.TESTNET),
        network=bdk.Network.TESTNET,
        database_config=db_config,
    )
    return wallet

def get_wallet_name_list():
    wallet_dir = './wallets'  # Replace with the actual path to your wallets directory
    wallet_names = []

    # List all files in the wallets directory
    files = os.listdir(wallet_dir)

    # Iterate through the files and extract wallet names without the extension
    for file in files:
        if file.endswith('.json'):
            wallet_name = os.path.splitext(file)[0]
            wallet_names.append(wallet_name)

    return wallet_names

def name_to_wallet(name, w_map):
    if name in w_map:
        return w_map[name]
    else:
        wallet_json = name_to_wallet_json(name)
        w_map[name] = wallet_from_file(wallet_json)
        return w_map[name]

def get_wallet_map():
    wallet_map = {}
    for name in get_wallet_name_list():
        wallet_map[name] = name_to_wallet(name, wallet_map)
    return wallet_map


wallet_map = get_wallet_map()



# print new receive address
def get_next_rx_address(wallet):
    address_info = wallet.get_address(bdk.AddressIndex.LAST_UNUSED())
    address = address_info.address
    index = address_info.index
    # print(f"New BIP84 testnet address: {address.as_string()} at index {index}")
    return address, index

def get_address_list(length, wallet):
    address_list = {}

    for i in range(0, length):
        address_info = wallet.get_address(bdk.AddressIndex.NEW())
        address_list[address_info.index] = address_info.address
        # print(f"New BIP84 testnet address: {address_info.address.as_string()} at index {address_info.index}")
    return address_list

def get_wallet_balance(wallet):
    # print wallet balance
    wallet.sync(blockchain, None) # TODO - how to sync without Blockchain config
    balance = wallet.get_balance()
    # print(f"Wallet balance is: {balance.total}")
    return balance.total

def write_json_to_file(file_name, json_content):
    f = open(file_name, "w")
    f.write(json_content)
    f.close()

def read_json_from_file(file_name):
    f = open(file_name, "r")
    return json.loads(f.read())

def get_wallet_balances_json(wallet_map):
    balances = {}
    for name in wallet_map.keys():
        balances[name] = get_wallet_balance(wallet_map[name])
    return json.dumps(balances, indent=2)


def get_changed_keys(old_balances, new_balances):
    all_keys = set(old_balances.keys()).union(new_balances.keys())
    # Add missing keys to old_balances and new_balances
    for name in all_keys:
        if name not in old_balances:
            old_balances[name] = 0
        if name not in new_balances:
            new_balances[name] = 0

    changed_keys = set(k for k in all_keys if old_balances.get(k) != new_balances.get(k))
    return changed_keys

def log_balances(changes_dataframe, db_name = "./balances/old_balances.json"):
    # get the directory of db_name
    db_dir = os.path.dirname(db_name)
    filename = db_dir + "/old_balances_" + str(int(time.time())) + ".json"
    # write changes_dataframe to filename as a json
    write_json_to_file(filename, changes_dataframe.to_json(orient='index'))


def monitor_wallet_balances(db_name = "./balances/balances.json"):
    if not os.path.exists(db_name):
        write_json_to_file(db_name, "{}")
    old_balances = read_json_from_file(db_name)
    new_balances = get_wallet_balances_json(wallet_map)
    changed_keys = get_changed_keys(old_balances, json.loads(new_balances))

    # if changed_keys is not an empty set
    if changed_keys:
        df = pd.DataFrame({'old': old_balances, 'new': new_balances}, index=changed_keys)
        log_balances(df, db_name)
        # Overwrite old_balances with new_balances
        write_json_to_file(db_name, new_balances)
        return df
    return None

"""
# TODO: Make pytest testcases based on this...
for name in wallet_map.keys():
    print("BIP84 testnet addresses:\n", str(get_address_list(length=0, wallet=wallet_map[name])))

for name in wallet_map.keys():
    print("Next BIP84 address for ", name, ":", str(get_next_rx_address(wallet_map[name])[0].as_string()))

for name in wallet_map.keys():
    print("Wallet balance for ", name, ":", str(get_wallet_balance(wallet_map[name])))

while True:
    time.sleep(1)
    changes = monitor_wallet_balances()
    if changes is not None:
        print(changes)
"""



#########FOR BROADCASTING##################
# devPath = devPath=str(args[1])
# interface = meshtastic.serial_interface.SerialInterface(devPath=devPath)
# print(f"Broadcasting address {address} on port {devPath}")
# interface.sendText(f"{address}")
