from Pyro5.api import locate_ns, Proxy
import numpy as np

HOST_IP = "raspberrypi.local"    # Set accordingly (i.e. "192.168.1.99")
HOST_PORT = 9090        # Set accordingly (i.e. 9876)

class Viewer(object):
    def __init__(self):
        self.uri = None

    def simplestart(self):
        market = self.uri
        print(market.name)
        exp = 100
        while True:
            exp+=100
            print(market.control(exp,1))  
            ims = market.images()
            ims = [np.array(im) for im in ims]
            print(ims)
            
                

    def start(self):
        quote_sources = {
            market.name: market.quotes() for market in self.uri
        }
        img_sources = {
            market.name: market.images() for market in self.uri
        }
        while True:
            for market, quote_source in quote_sources.items():
                quote = next(quote_source)  # get a new stock quote from the source
                symbol, value = quote
                print("{0}.{1}: {2}".format(market, symbol, value))
            for market in self.uri:
                print(market.control(10000,4))  
                print(np.mean(market.images()))  
                


def find_uri():
    # You can hardcode the stockmarket names for nasdaq and newyork, but it
    # is more flexible if we just look for every available stockmarket.
    uri = None
    with locate_ns(host = HOST_IP, port=HOST_PORT, broadcast=False) as ns:
        print("found ns", ns)

        for market, market_uri in ns.list(prefix="example.stockmarket").items():
            print("found market", market)
            if market == 'example.stockmarket.raspberry':
                uri=(Proxy(market_uri))
    if not uri:
        raise ValueError("no uri found! (have you started the stock uri first?)")
    return uri


def main():
    viewer = Viewer()
    viewer.uri = find_uri()
    viewer.simplestart()


if __name__ == "__main__":
    main()
