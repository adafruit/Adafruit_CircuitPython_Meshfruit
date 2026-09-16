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


CircuitPython helper to decode LoRa mesh packets.

Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://circuitpython.org/libraries>`_
or individual libraries can be installed using
`circup <https://github.com/adafruit/circup>`_.

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

    import adafruit_rfm9x
    import board
    import digitalio
    
    import adafruit_meshfruit
    
    FREQUENCY = 906.875
    CHANNEL_HASH = 0x08
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
    
    mesh = adafruit_meshfruit.Meshtastic_Compatible()
    
    print("listening on", FREQUENCY, "MHz")
    
    while True:
        raw = rfm9x.receive(with_header=True, timeout=5.0)
        if raw is None:
            continue
        if len(raw) <= adafruit_meshfruit.HEADER_LEN:
            continue
    
        packet = mesh.decode(raw)
        if packet.channel_hash != CHANNEL_HASH:
            continue
    
        if packet.portnum == adafruit_meshfruit.PORT_TEXT_MESSAGE and packet.payload:
            print(packet.sender_id, packet.text)

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
