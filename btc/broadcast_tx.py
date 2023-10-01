import bdkpython as bdk
import meshtastic.serial_interface
import sys
from segment import Segment
from monitor_balances import monitor_wallet_balances
from monitor_balances import wallet_from_file
from monitor_balances import get_wallet_map
from monitor_balances import get_blockchain_config
from monitor_balances import get_wallet_balances_json
from monitor_balances import name_to_wallet
from monitor_balances import get_next_rx_address
import json
import time
import uuid
import random
import hashlib

blockchain_config = get_blockchain_config()
blockchain = bdk.Blockchain(blockchain_config)
wallet_map = get_wallet_map()

def invert_map(to_invert):
    inverted = {}
    for wallet in to_invert.keys():
        balance = to_invert[wallet]
        inverted[balance] = wallet
    return inverted

def get_smallest(balances_list):
    min = sys.maxsize
    for balance in balances_list:
        if balance < min:
            min = balance
    return min

def get_largest(balances_list):
    max = 0
    for balance in balances_list:
        if balance > max:
            max = balance
    return max

def get_sender_and_receiver_name():
    wallet_balances = json.loads(get_wallet_balances_json(wallet_map))
    balances_wallet = invert_map(wallet_balances)

    balances = list(balances_wallet.keys())
    names = set(wallet_balances.keys())

    sending_wallet_name = balances_wallet[get_largest(balances)]
    potential_recipients = list(names - {sending_wallet_name})
    receiving_wallet_name = random.choice(potential_recipients)

    return sending_wallet_name, receiving_wallet_name


def get_transaction(verbose = False):

    sender, receiver = get_sender_and_receiver_name()
    sender_wallet = name_to_wallet(sender, wallet_map)
    receiver_wallet = name_to_wallet(receiver, wallet_map)
    receiver_address, index = get_next_rx_address(receiver_wallet)

    if verbose:
        print(f"Sender balance = {sender_wallet.get_balance()}")
        print(f"Receiver balance = {receiver_wallet.get_balance()}")
        print(f"Send top-up to = {receiver_address.as_string()}")

    tx = bdk.TxBuilder().add_recipient(receiver_address.script_pubkey(), 1000).finish(sender_wallet)
    if verbose:
        print(f"transaction_details = {tx.transaction_details}")

    return tx, sender_wallet


def sign_transaction(verbose = False):

    tx, sender_wallet = get_transaction(verbose)
    psbt = tx.psbt

    signed_psbt = sender_wallet.sign(psbt, sign_options=None)
    raw_transaction = psbt.extract_tx()

    if verbose:
        print(f"signed_psbt = {signed_psbt}")

    return raw_transaction, tx


def get_mac_address():
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    formatted_mac = ":".join([mac[e:e+2] for e in range(0, 12, 2)])
    return formatted_mac

def get_device_id(length=4):
    device_mac = str(get_mac_address())
    checksum = hashlib.sha256(device_mac.encode()).hexdigest()
    return str(checksum[:length])

def get_message_id(message, length=4):
    checksum = hashlib.sha256(str(message).encode()).hexdigest()
    return str(checksum[:length])

def get_transaction_segments(verbose = False, network = 't'):

    raw_transaction, tx = sign_transaction(verbose)
    did, mid = get_device_id(), get_message_id(raw_transaction.serialize())

    if verbose:
        strHexTx = ''.join(map(lambda x: format(x, '02x'), raw_transaction.serialize()))
        print(f"strHexTx = {strHexTx}")

    # Would be cooler if type Transaction implemented segment()
    segments = Segment.tx_to_segments(
        device_id=did,
        strHexTx=raw_transaction.serialize(),
        strHexTxHash=tx.transaction_details.txid,
        messageIdx=mid,
        network=network,
        isZ85=False
    )

    return segments, did, mid

def listen_for_ack(interface, mid):
    while True:
        packet = interface.waitForPacket()
        if 'decoded' in packet and 'portnum' in packet['decoded'] and packet['decoded']['portnum'] == 'PRIVATE_APP':
            s = Segment.deserialize(packet['decoded']['payload'])
            if s.message_id == mid:
                print(f"Received ACK for message {mid}")
                break

# def send_ack()

def send_segment(interface, seg):
    print(f"Broadcasting {{{seg}}} to mesh")
    interface.sendData(seg.serialize(), wantAck=True)
    time.sleep(10)  # Give the receiver some time to process this

def send_transaction(devPath):
    segments, did, mid = get_transaction_segments(verbose=True, network='t')
    interface = meshtastic.serial_interface.SerialInterface(devPath=devPath)
    
    print(f"Broadcasting {did}:{mid} over mesh in {len(segments)} parts")
    for seg in segments:
        send_segment(interface, seg)


if len(sys.argv) != 2:
    print("Please select a device that you want to broadcase the transaction from")
    print("Usage: python script.py /dev/ttyACM*")
    sys.exit(1)  # Exit with an error code

devPath = str(sys.argv[1])

if not devPath.startswith("/dev/ttyACM"):
    print("The provided path does not match the expected format /dev/ttyACM*")
    sys.exit(1)  # Exit with an error code

print(f"devPath = {devPath}")
send_transaction(devPath)
