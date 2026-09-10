# SPDX-FileCopyrightText: 2026 Pedro Ruiz for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_meshfruit`
================================================================================

Decode LoRa mesh packets compatible with the Meshtastic protocol.

Receive only. This module takes raw packet bytes and returns decoded
content. It does not touch a radio, so the same code works over LoRa,
UDP, or a file of captured packets, and it can be tested with no
hardware attached.

Channel broadcasts encrypted with a shared PSK are supported. PKI
encrypted direct messages are not: those use per-node X25519 keys,
which CircuitPython has no support for.

* Author(s): Pedro Ruiz

Implementation Notes
--------------------

**Hardware:**

Any LoRa radio able to receive on the mesh's physical layer, for
example the `Adafruit RFM95W LoRa Radio Transceiver Breakout
<https://www.adafruit.com/product/3072>`_ (Product ID: 3072). The
module itself is hardware independent and also decodes packets
captured from any other source.

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

* The ``aesio`` core module, built into CircuitPython.

"""

import aesio
from micropython import const

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Meshfruit.git"

HEADER_LEN = 16
_CHANNEL_HASH_OFFSET = const(13)

PORT_TEXT_MESSAGE = 1
PORT_POSITION = 3
PORT_NODEINFO = 4

# The base default PSK from the firmware source, src/mesh/Channels.h.
# A one-byte PSK is shorthand for "default key N": the firmware expands
# it to these 16 bytes with the final byte replaced by N. The familiar
# "AQ==" is the single byte 0x01, giving this array unchanged.
# Verified against base64 1PG7OiApB1nwvP+rz05pAQ==
DEFAULT_KEY_BASE = bytes.fromhex("d4f1bb3a20290759f0bcffabcf4e6901")

# Convenience alias for the default LongFast channel key.
DEFAULT_KEY = DEFAULT_KEY_BASE


def expand_psk(psk):
    """Expand a channel PSK into a usable AES key.

    Accepts the three forms a channel can carry: one byte, which is
    shorthand for a built-in default key and replaces the last byte of
    :const:`DEFAULT_KEY_BASE`; sixteen bytes, used directly as an
    AES-128 key; or thirty-two bytes, used directly as an AES-256 key.

    :param bytes psk: The channel pre-shared key, 0, 1, 16 or 32 bytes
    :return: The expanded key, or None if the channel is unencrypted
    :rtype: bytes

    :raises ValueError: if the PSK is not one of the accepted lengths
    """
    psk = bytes(psk)
    if len(psk) == 0:
        return None
    if len(psk) == 1:
        if psk[0] == 0:
            return None
        return DEFAULT_KEY_BASE[:-1] + psk
    if len(psk) in {16, 32}:
        return psk
    raise ValueError("PSK must be 0, 1, 16, or 32 bytes")


def read_varint(buf, index):
    """Read a protobuf varint.

    :param bytes buf: Buffer to read from
    :param int index: Offset to start reading at
    :return: The decoded value and the offset just past it
    :rtype: tuple
    """
    value = 0
    shift = 0
    while index < len(buf):
        byte = buf[index]
        index += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            break
        shift += 7
    return value, index


def parse_data(buf):
    """Walk a Data protobuf.

    :param bytes buf: Decrypted packet payload
    :return: The port number and the payload bytes, either of which may
        be None if the field was absent
    :rtype: tuple
    """
    portnum = None
    payload = None
    index = 0
    while index < len(buf):
        tag, index = read_varint(buf, index)
        wire = tag & 0x07
        # A tag with no room left for its value means the buffer was
        # truncated. Stop rather than inventing an empty field.
        if index >= len(buf) and wire in {0, 2}:
            break
        field = tag >> 3
        if wire == 0:
            value, index = read_varint(buf, index)
            if field == 1:
                portnum = value
        elif wire == 2:
            length, index = read_varint(buf, index)
            chunk = buf[index : index + length]
            index += length
            if field == 2:
                payload = chunk
        elif wire == 5:
            index += 4
        elif wire == 1:
            index += 8
        else:
            break
    return portnum, payload


def parse_user(buf):
    """Walk a User protobuf from a NodeInfo payload.

    Field numbers follow the User message in the protocol's protobuf
    definitions and were confirmed against a captured packet.

    :param bytes buf: Payload of a :const:`PORT_NODEINFO` message
    :return: Any of ``id``, ``long_name`` and ``short_name`` that were
        present, each as raw bytes
    :rtype: dict
    """
    result = {}
    index = 0
    while index < len(buf):
        tag, index = read_varint(buf, index)
        wire = tag & 0x07
        if index >= len(buf) and wire in {0, 2}:
            break
        field = tag >> 3
        if wire == 0:
            _, index = read_varint(buf, index)
        elif wire == 2:
            length, index = read_varint(buf, index)
            chunk = buf[index : index + length]
            index += length
            if field == 1:
                result["id"] = chunk
            elif field == 2:
                result["long_name"] = chunk
            elif field == 3:
                result["short_name"] = chunk
        elif wire == 5:
            index += 4
        elif wire == 1:
            index += 8
        else:
            break
    return result


def decode_text(raw):
    """Decode protobuf string bytes.

    :param bytes raw: Bytes to decode, or None
    :return: The decoded string, or None if raw was None or not UTF-8
    :rtype: str
    """
    if raw is None:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeError:
        return None


def build_nonce(packet):
    """Build the 16-byte AES-CTR initialization vector for a packet.

    The firmware uses the packet ID concatenated with the sender node
    number as a 96-bit nonce, with a 32-bit block counter in the low
    bytes. The packet ID is a uint32 that is zero-extended to 64 bits.

    :param bytes packet: A complete packet, header included
    :return: The 16 byte initialization vector
    :rtype: bytes
    """
    packet_id = bytes(packet[8:12])
    sender = bytes(packet[4:8])
    return packet_id + bytes(4) + sender + bytes(4)


def decrypt(packet, key=DEFAULT_KEY):
    """Decrypt a packet's payload.

    A fresh AES object is built per packet because CTR mode keeps a
    stateful counter that must not carry across messages.

    :param bytes packet: A complete packet, header included
    :param bytes key: The expanded channel key. Defaults to
        :const:`DEFAULT_KEY`
    :return: The decrypted payload
    :rtype: bytearray
    """
    ciphertext = packet[HEADER_LEN:]
    plaintext = bytearray(len(ciphertext))
    aesio.AES(key, aesio.MODE_CTR, build_nonce(packet)).encrypt_into(ciphertext, plaintext)
    return plaintext


def sender_id(packet):
    """Return the sender node ID as a bang-prefixed hex string.

    :param bytes packet: A complete packet, header included
    :return: The node ID, for example ``!09d43fc8``
    :rtype: str
    """
    return f"!{int.from_bytes(packet[4:8], 'little'):08x}"


def channel_hash(packet):
    """Return the channel hash byte used to filter incoming packets.

    :param bytes packet: A complete packet, header included
    :return: The channel hash
    :rtype: int
    """
    return packet[_CHANNEL_HASH_OFFSET]
