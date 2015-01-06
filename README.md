Project Vanguard
========

A space program for the Web

v0.1 - Stratosphere (HABs)
---

Enable JS based experiments on the Beaglebone Black using High Altitude Balloons
for R&D

#### High level hardware BoM

- [BeagleBone Black Rev B/C](http://beagleboard.org/BLACK)
- [RadiumBoards HD Camera Cape for BeagleBone Black](http://radiumboards.com/HD_Camera_Cape_for_BeagleBone_Black.php)
- [Argent Data FC301/D UHF 5W Data Radio](https://www.argentdata.com/catalog/product_info.php?products_id=107)
- [TNC-Black](http://tnc-x.com/TNCBlack.htm)
- A Custom Find-Me Cape with:
    - [MediaTek MT3339 GPS chip](http://www.mediatek.com/en/products/connectivity/gps/mt3333/) (also used in the Adafruit Ultimate GPS)
    - [RadioMetrix TX2H 433MHz 25mW transmitter](http://www.radiometrix.com/content/tx2h)
    - [Freescale MPL3115A2 Altimeter and Pressure Sensor](http://www.freescale.com/webapp/sps/site/prod_summary.jsp?code=MPL3115A2)
    - [Mallory Sonalert PS-562Q 100dB Alert Speaker](http://www.mouser.com/ProductDetail/Mallory-Sonalert/PS-562Q/?qs=SJZ%252bTX%252bI2BSbY9EFn3cy2Q%3D%3D)
    - [Internal and external 10K thermistors @ 25C](http://www.adafruit.com/product/372)

A detailed list of pin usage is maintained in [PINS.md](PINS.md)

#### Software requirements

- [Debian 7 with recent gnueabihf kernel](http://www.armhf.com/download/)
- APT packages:

        $ sudo apt-get install gpsd streamer build-essential python python-dev python-setuptools python-pip python-smbus
- Python packages:

        $ sudo pip install -r payload/requirements.txt
- [Adafruit BBIO Python Library](https://learn.adafruit.com/setting-up-io-python-library-on-beaglebone-black/installation-on-ubuntu)
- [NodeJS v0.10.16](http://www.armhf.com/node-js-for-the-beaglebone-black/)

#### Configuration

See [payload/config/config.json](payload/config/config.json)
