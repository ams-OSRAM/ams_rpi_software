"""
Description:
this script connects to a remote raspberry pi via usb/ethernet
and captures images
Author:
philippe.baetens@ams-osram.com
Use:
pip install -r requirements.txt
python pyro5testpi.py
"""

from Pyro5.api import locate_ns, Proxy
import numpy as np
import Pyro5

HOST_IP = Pyro5.socketutil.get_ip_address('raspberrypi.local', version=4)
HOST_PORT = 9091        # Set accordingly (i.e. 9876)

class Viewer(object):
    def __init__(self):
        self.uri = None

    def simplestart(self):
        market = self.uri
        market.start_server()
        print(market.name)
        exp = 100
        exp+=100
        print(market.control(exp,1))  
        ims = market.images(1)
        ims = [np.array(im) for im in ims]
        print(ims[0].mean())
        market.stop_server() 


def find_uri():
    uri = None
    with locate_ns(host = HOST_IP, port=HOST_PORT, broadcast=True) as ns:
        print("found ns", ns)
        for market, market_uri in ns.list(prefix="ams").items():
            print("found remote nameserver", market)
            if market == 'ams.raspberry':
                uri=(Proxy(market_uri))
    if not uri:
        raise ValueError("no uri found! (have you started the stock uri first?)")
    return uri



if __name__ == "__main__":
    viewer = Viewer()
    viewer.uri = find_uri()
    viewer.simplestart()
