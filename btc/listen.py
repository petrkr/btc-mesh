import time
import meshtastic
import bdkpython
import meshtastic.serial_interface
from pubsub import pub
import sys
import pprint
import json

import bdkpython as bdk

from segment import Segment
from segment_storage import SegmentStorage

args = sys.argv

blockchain_config = bdk.BlockchainConfig.ELECTRUM(
    # params: url, socks5, retry, timeout, stop_gap, validate_domain
    bdk.ElectrumConfig(
        "ssl://electrum.blockstream.info:60002",
        None,
        5,
        None,
        100,
        True,
    )
)
blockchain = bdk.Blockchain(blockchain_config)

# Initialize object to store received packets
storage = SegmentStorage()

import os
import time

devPath=str(args[1])
print(f"devPath = {devPath}")

# Initialize interface for receiving messages over mesh
interface = meshtastic.serial_interface.SerialInterface(devPath)


def onReceive(packet, interface): # called when a packet arrives
    if 'decoded' in packet and 'portnum' in packet['decoded'] and packet['decoded']['portnum'] == 'PRIVATE_APP': # packet['decoded']['portnum'] == 'TEXT_MESSAGE_APP':
        s = Segment.deserialize(packet['decoded']['payload'])
        storage.put(s)

        print(f"{s}")

        print("payload_id, ", str(s.payload_id))
        print("sequence number, ", str(s.sequence_num))
        print("segment_count, ", str(s.segment_count))
        print("segment_status: ", storage.get_segment_status(s.payload_id))

        # TODO: is_complete seems to be counting the number of segments, but it doesn't seem to check if all the segments belong to the same transaction
        # TODO: Send back feedback, so that the sender knows which segments were received.
        # TODO: Monitor wallet balances
        if storage.is_complete(s.payload_id):
            tx_id = storage.get_transaction_id(s.payload_id)
            trx_segments = storage.get_by_transaction_id(tx_id)
            raw_tx = storage.get_raw_tx(trx_segments)
            to_broadcast = ''.join(map(lambda x: format(x, '02x'), raw_tx))
            print(f"Broadcasting trx: {to_broadcast}")
            bdk_trx = bdk.Transaction(raw_tx) # bytes.fromhex(
            blockchain.broadcast(bdk_trx)
            print(f"Successfully broadcasted: {tx_id}")
        else:
            print("Activity matches our filter, storage is incomplete though.")
    else:
        print("Detected other activity on the mesh.")


def onConnection(interface, topic=pub.AUTO_TOPIC): # called when we (re)connect to the radio
    print("ping7")
    interface.sendText(f"Connected to device: {args[1]}") # defaults to broadcast, specify a destination ID if you wish

pub.subscribe(onReceive, "meshtastic.receive") # could use meshtastic.receive.data.portnum to listen for specific events

while True:
    time.sleep(1000)
