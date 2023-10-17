# About

`py-pcsc-terminal` is an interactive command line (CLI) tool for PC/SC that can send, receive and parse APDU for PC/SC readers.

It's something like [scriptor](https://github.com/LudovicRousseau/pcsc-tools/blob/master/scriptor), but written in python.


# Quick start

Checkout and switch to repository:

~~~
git clone git@github.com:sigsergv/py-pcsc-terminal.git
cd py-pcsc-terminal
~~~

For debian/ubuntu install required packages:

~~~
sudo apt install pcscd libpcsclite-dev
~~~

Initialize virtual environment:

~~~
python3 -m venv .venv
source .venv/bin/activate
pip install wheel swig
pip install -r requirements.txt
~~~

Run terminal:

~~~
./py-pcsc-terminal
~~~
