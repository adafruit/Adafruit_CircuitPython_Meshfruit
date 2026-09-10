# SPDX-FileCopyrightText: 2026 Pedro Ruiz for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""Listen for mesh broadcast messages and print them.

Wire an RFM95W breakout to the SPI bus with CS on D11 and RST on D12.
Another node on the same channel needs to be sending for anything to
appear.
"""

import adafruit_rfm9x
import board
import digitalio

import adafruit_meshfruit

# US 915MHz band, slot 20, which is where the default public channel
# lands. Elsewhere this has to match the nodes around you.
FREQUENCY = 906.875

# Channel hash for the default public channel.
CHANNEL_HASH = 0x08

# The mesh uses a different LoRa sync word to the library default, and
# it has to be written straight to the radio's register.
SYNC_WORD_REG = 0x39
SYNC_WORD = 0x2B

rfm9x = adafruit_rfm9x.RFM9x(
    board.SPI(),
    digitalio.DigitalInOut(board.D11),
    digitalio.DigitalInOut(board.D12),
    FREQUENCY,
)
rfm9x.signal_bandwidth = 250000
rfm9x.spreading_factor = 11
rfm9x.coding_rate = 5
rfm9x.preamble_length = 16
rfm9x.enable_crc = True
rfm9x._write_u8(SYNC_WORD_REG, SYNC_WORD)  # noqa: SLF001

print("listening on", FREQUENCY, "MHz")

while True:
    packet = rfm9x.receive(with_header=True, timeout=5.0)
    if packet is None:
        continue
    if len(packet) <= adafruit_meshfruit.HEADER_LEN:
        continue
    if adafruit_meshfruit.channel_hash(packet) != CHANNEL_HASH:
        continue

    plaintext = adafruit_meshfruit.decrypt(packet)
    portnum, payload = adafruit_meshfruit.parse_data(plaintext)
    if portnum == adafruit_meshfruit.PORT_TEXT_MESSAGE and payload:
        print(
            adafruit_meshfruit.sender_id(packet),
            adafruit_meshfruit.decode_text(payload),
        )
