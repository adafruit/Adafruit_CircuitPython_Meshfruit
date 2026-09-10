Introduction
============


.. image:: https://readthedocs.org/projects/adafruit-circuitpython-meshfruit/badge/?version=latest
    :target: https://docs.circuitpython.org/projects/meshfruit/en/latest/
    :alt: Documentation Status


.. image:: https://raw.githubusercontent.com/adafruit/Adafruit_CircuitPython_Bundle/main/badges/adafruit_discord.svg
    :target: https://adafru.it/discord
    :alt: Discord


.. image:: https://github.com/adafruit/Adafruit_CircuitPython_Meshfruit/workflows/Build%20CI/badge.svg
    :target: https://github.com/adafruit/Adafruit_CircuitPython_Meshfruit/actions
    :alt: Build Status


.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
    :target: https://github.com/astral-sh/ruff
    :alt: Code Style: Ruff


Decode LoRa mesh packets in CircuitPython.

This library is compatible with the Meshtastic protocol. It is not
Meshtastic, is not affiliated with or endorsed by the Meshtastic
project, and does not implement a Meshtastic node.

**Receive only.** The library turns raw packet bytes into decoded
content. It does not transmit, does not participate in mesh routing,
and a board using it will not appear in anyone's node list.

It never touches a radio, so the same code works over LoRa, over UDP,
or against a file of captured packets, and it can be tested with no
hardware attached.

What it does
------------

* Decrypts channel broadcasts encrypted with a shared PSK (AES-CTR)
* Expands the one byte default PSK shorthand as well as 16 and 32 byte keys
* Walks the Data protobuf without a protobuf library
* Parses text messages and NodeInfo user records

What it does not do
-------------------

* **Transmit.** Nothing here builds or sends packets.
* **PKI direct messages.** Those use per node X25519 keys, which
  CircuitPython has no support for. Channel broadcasts are unaffected.
* **Radio configuration.** See the settings table below.


Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_

The core module ``aesio`` is built into CircuitPython. Please ensure all
dependencies are available on the CircuitPython filesystem. This is easily
achieved by downloading `the Adafruit library and driver bundle
<https://circuitpython.org/libraries>`_.

Installing from PyPI
=====================

On supported GNU/Linux systems like the Raspberry Pi, you can install the driver
locally `from PyPI <https://pypi.org/project/adafruit-circuitpython-meshfruit/>`_.
To install for current user:

.. code-block:: shell

    pip3 install adafruit-circuitpython-meshfruit

Installing to a Connected CircuitPython Device with Circup
==========================================================

Make sure that you have ``circup`` installed in your Python environment.
Install it with the following command if necessary:

.. code-block:: shell

    pip3 install circup

With ``circup`` installed and your CircuitPython device connected use the
following command to install:

.. code-block:: shell

    circup install adafruit_meshfruit

Usage Example
=============

.. code-block:: python

    from adafruit_meshfruit import meshtastic

    packet = bytes.fromhex(
        "ffffffffc83fd409d734952c630800c86869e3bd000649b1ff995fcb"
    )

    if meshtastic.channel_hash(packet) == 0x08:
        plain = meshtastic.decrypt(packet)
        port, body = meshtastic.parse_data(plain)
        if port == meshtastic.PORT_TEXT_MESSAGE:
            print(meshtastic.sender_id(packet), meshtastic.decode_text(body))

Radio settings
==============

The library does not configure a radio, but a receiver has to match the
sender's physical layer. For the US LongFast preset:

=========================  ============
Setting                    Value
=========================  ============
Bandwidth                  250 kHz
Spreading factor           11
Coding rate                5
Preamble length            16
CRC                        enabled
Sync word (register 0x39)  ``0x2B``
Frequency slot 20          906.875 MHz
=========================  ============

The sync word is the detail most likely to catch you out:
``adafruit_rfm9x`` defaults to ``0x12``, and the value used here has to
be written directly to register ``0x39``.

Slot ``N`` in the US band sits at ``902.125 + (N - 1) * 0.25`` MHz.

Verification
============

The default channel key and the AES-CTR nonce layout were checked
against the protocol's firmware source rather than inferred. The
NodeInfo field numbers were confirmed against a packet captured off
the air.

Documentation
=============

API documentation for this library can be found on `Read the Docs
<https://docs.circuitpython.org/projects/meshfruit/en/latest/>`_.

For information on building library documentation, please check out
`this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/adafruit/Adafruit_CircuitPython_Meshfruit/blob/HEAD/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.
