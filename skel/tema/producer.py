"""
    Producer class - Producer implementation
    332CA - Brinzan Darius-Ionut
"""

from threading import Thread
from time import sleep

class Producer(Thread):
    """
    Class that represents a producer.
    """
    
    def __init__(self, products, marketplace, republish_wait_time, **kwargs):
        """
        Constructor.

        @type products: List()
        @param products: a list of products that the producer will produce

        @type marketplace: Marketplace
        @param marketplace: a reference to the marketplace

        @type republish_wait_time: Time
        @param republish_wait_time: the number of seconds that a producer must
        wait until the marketplace becomes available

        @type kwargs:
        @param kwargs: other arguments that are passed to the Thread's __init__()
        """
        Thread.__init__(self, **kwargs)
        self.products = products
        self.marketplace = marketplace
        self.republish_wait_time = republish_wait_time
        self.kwargs = kwargs

    def run(self):
        """ Run function of producer class 
            Allows a producer object to publish products -> Marketplace obj
        """
        # register a new producer
        producer_id = self.marketplace.register_producer()
        while True:
            # iterate through -> publish the prod to market
            for event_product, quantity, wait_time in self.products:
                for _ in range(quantity):
                    # true -> publish and waits before publishing next item
                    if self.marketplace.publish(producer_id, event_product):
                        sleep(wait_time)
                    else:
                        sleep(self.republish_wait_time)
                        break
