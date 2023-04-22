"""
    Consumer class - Consumer implementation
    332CA - Brinzan Darius-Ionut
"""

from threading import Thread
from time import sleep

class Consumer(Thread):
    """
    Class that represents a consumer.
    """

    def __init__(self, carts, marketplace, retry_wait_time, **kwargs):
        """
        Constructor.

        :type carts: List
        :param carts: a list of add and remove operations

        :type marketplace: Marketplace
        :param marketplace: a reference to the marketplace

        :type retry_wait_time: Time
        :param retry_wait_time: the number of seconds that a producer must wait
        until the Marketplace becomes available

        :type kwargs:
        :param kwargs: other arguments that are passed to the Thread's __init__()
        """
        Thread.__init__(self, **kwargs)
        self.kwargs = kwargs
        self.carts = carts
        self.marketplace = marketplace
        self.retry_wait_time = retry_wait_time

    def run(self):
        def add_to_cart(cart_id, product, quantity):
            """ Add a specified quant of a prod to the consumer
                cart. Adds quantity and if it fails retry after
                a specified amount of time. """
            count = 0
            while count < quantity:
                if self.marketplace.add_to_cart(cart_id, product):
                    count += 1
                else:
                    sleep(self.retry_wait_time)

        def remove_from_cart(cart_id, product, quantity):
            """ Remove specified quantity of a specified prod from cart"""
            for _ in range(quantity):
                self.marketplace.remove_from_cart(cart_id, product)

        operation_funcs = {
            "add": add_to_cart,
            "remove": remove_from_cart
        }

        output_lines = []

        for cart in self.carts:
            # creates new cart
            cart_id = self.marketplace.new_cart()
            # check operation type if it is add or remove
            for operation in cart:
                operation_type = operation["type"]
                operation_func = operation_funcs.get(operation_type, lambda *args: None)
                operation_func(cart_id, operation["product"], operation["quantity"])
            # place the order
            products = self.marketplace.place_order(cart_id)
            # append each bought prod to the output list
            for product in products:
                output_lines.append(f"{self.name} bought {product}")

        output = "\n".join(output_lines)

        with self.marketplace.order_lock:
            print(output)
