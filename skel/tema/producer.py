from threading import Thread
from time import sleep

class Producer(Thread):

    def __init__(self, products, marketplace, republish_wait_time, **kwargs):
        Thread.__init__(self, **kwargs)
        self.products = products
        self.marketplace = marketplace
        self.republish_wait_time = republish_wait_time
        self.kwargs = kwargs

    def run(self):

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
