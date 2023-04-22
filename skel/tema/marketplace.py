"""
    Marketplace class - Marketplace implementation
    332CA - Brinzan Darius-Ionut
"""
from threading import Lock
import logging
import unittest


class Marketplace:
    """
    Class that represents the Marketplace. It's the central part of the implementation.
    The producers and consumers use its methods concurrently.
    """
    
    def __init__(self, queue_size_per_producer):
        """
        Constructor

        :type queue_size_per_producer: Int
        :param queue_size_per_producer: the maximum size of a queue associated with each producer
        """
        self.queue_size_per_producer = queue_size_per_producer
        self.data = {
            'producers_products': {},
            'consumers_carts': {},
            'all_products': {},
        }
        # used to generate ids for producers and consumers carts
        self.producer_id, self.cart_id = 0, 0

        # make sure one thread each time for
        # cart, producer, order
        self.cart_lock = Lock()
        self.producer_lock = Lock()
        self.order_lock = Lock()

        self.logger = self.configure_logger()

    def configure_logger(self):
        """ logger used for logging helping for debug """
        logging.basicConfig(
            level=logging.DEBUG,
            filename='marketplace.log',
            filemode='w',
            format='[%(asctime)s] - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        return logging.getLogger()

    def register_producer(self):
        """
        Returns an id for the producer that calls this.
        """
        producer_id = None
        try:
            # using producer_lock -> make sure that only one thread at a time access
            self.producer_lock.acquire()
            producer_id = self.producer_id
            # increment for uniq id
            self.producer_id += 1
            # init an empty list that prod can add to marketplace
            self.data['producers_products'][producer_id] = []
            self.logger.info("Registering producer .. , id: %s", producer_id)
        except Exception as exc_catch:
            self.logger.error("Error registering producer .. : %s", str(exc_catch))
        finally:
            self.producer_lock.release()
            return producer_id

    def publish(self, producer_id, product):
        """
        Adds the product provided by the producer to the marketplace

        :type producer_id: String
        :param producer_id: producer id

        :type product: Product
        :param product: the Product that will be published in the Marketplace

        :returns True or False. If the caller receives False, it should wait and then try again.
        """
        try:
            # add prod to the list of published
            self.data['producers_products'][producer_id].append(product)
            self.logger.info(
                "Producer %d published %s", producer_id, product.__str__())
            # update dict to include new products
            self.data['all_products'][product] = producer_id
            return True
        except Exception as exc_catch:
            self.logger.error("Error publishing the product: %s", str(exc_catch))
            return False

    def new_cart(self):
        """
        Creates a new cart for the consumer

        :returns an int representing the cart_id
        """
        with self.cart_lock:
            try:
                cart_id = self.cart_id
                # increment for uniq id
                self.cart_id += 1
                # new cart -> adding and empty list
                self.data['consumers_carts'][cart_id] = []
                self.logger.info("Created new cart with id: %d", cart_id)
            except Exception as exc_catch:
                self.logger.error("Error creating new cart: %s", str(exc_catch))
            finally:
                return cart_id

    def add_to_cart(self, cart_id, product):
        """
        Adds a product to the given cart. The method returns

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to add to cart

        :returns True or False. If the caller receives False, it should wait and then try again
        """
        try:
            # I used the next function to find the id for the product
            id_producer = next((i for i in range(self.producer_id)
                                if product in self.data['producers_products'][i]), None)
            # If prod is available -> add to cart and put log message
            if id_producer is not None:
                self.data['consumers_carts'][cart_id].append(product)
                self.data['producers_products'][id_producer].remove(product)

                self.logger.info(f"Succesfully added a new product to the cart {cart_id}: {product}")
                self.logger.info(f"Succesfully removed a product from producer {id_producer}: {product}")

                return True
            return False
        except Exception as exc_catch:
            self.logger.error("Error adding product to cart: %s", str(exc_catch))
            return False

    def remove_from_cart(self, cart_id, product):
        """
        Removes a product from cart.

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to remove from cart
        """
        try:
            # if prod is in cart
            if product in self.data['consumers_carts'][cart_id]:
                # get id prod from all products of the prod
                producer_id = self.data['all_products'][product]
                # add prod to producer list & remove from cart
                self.data['producers_products'][producer_id].append(product)
                self.data['consumers_carts'][cart_id].remove(product)

                self.logger.info(
                    "Succesfully removed product %s from cart %d", product.__str__(), cart_id)
        except Exception as exc_catch:
            self.logger.error("Error removing product from cart: %s", str(exc_catch))

    def place_order(self, cart_id):
        """
        Return a list with all the products in the cart.

        :type cart_id: Int
        :param cart_id: id cart
        """
        with self.order_lock:
            try:
                # copy the products from cart
                order = self.data['consumers_carts'][cart_id].copy()
                # clear the cart
                self.data['consumers_carts'][cart_id].clear()
                # return order with the content of the cart
                self.logger.info(
                    "The order placed %s from cart with id: %d", order.__str__(), cart_id)
                return order
            except Exception as exc_catch:
                self.logger.error("Error placing order: %s", str(exc_catch))
                return []


"""
    UnitTest Marketplace - Test marketplace
"""


class TestMarketplace(unittest.TestCase):

    def setUp(self):
        # initialise setup for testing
        self.marketplace = Marketplace(10)
        self.producer_id = self.marketplace.register_producer()

    def get_product_dict(self):
        # one asset for testing
        return {
            "product_type": "Coffee",
            "name": "Eritreea",
            "acidity": 3.15,
            "roast_level": "HIGH",
            "price": 2.1
        }

    def test_register_producer(self):
        """ Test register """
        producer_id = self.marketplace.register_producer()
        self.assertEqual(producer_id, 1)

    def test_publish(self):
        """ Test publish """
        product_dict = self.get_product_dict()
        product = str(product_dict)
        # publish product
        result = self.marketplace.publish(self.producer_id, product)
        # if true => ensures that the product was published
        self.assertTrue(result)
        # makes sure that product was added to the list
        self.assertIn(product, self.marketplace.data['producers_products'][self.producer_id])
        # makes sure that all products dict is up with new product
        self.assertEqual(self.marketplace.data['all_products'][product], self.producer_id)

    def test_new_cart(self):
        """ Test new_cart """
        cart_id = self.marketplace.new_cart()
        # makes sure that new_cart is correctly init a new cart
        self.assertEqual(cart_id, 0)

    # test add
    def test_add_to_cart(self):
        """ Test add_to_cart """
        product_dict = self.get_product_dict()
        product = str(product_dict)
        # check if it published before adding to cart
        self.marketplace.publish(self.producer_id, product)

        cart_id = self.marketplace.new_cart()
        result = self.marketplace.add_to_cart(cart_id, product)
        # check if it is added to cart & add to correct cart & 
        # removed from the list of products by the prod
        self.assertTrue(result)
        self.assertIn(product, self.marketplace.data['consumers_carts'][cart_id])
        self.assertNotIn(product, self.marketplace.data['producers_products'][self.producer_id])

    # test remove
    def test_remove_from_cart(self):
        """ Test remove """
        product_dict = self.get_product_dict()
        product = str(product_dict)
        # check if published
        self.marketplace.publish(self.producer_id, product)
        # add to the cart
        cart_id = self.marketplace.new_cart()
        self.marketplace.add_to_cart(cart_id, product)
        # remove from cart -> add back to the list of published
        self.marketplace.remove_from_cart(cart_id, product)
        # check if removed & added back to list of prod
        self.assertNotIn(product, self.marketplace.data['consumers_carts'][cart_id])
        self.assertIn(product, self.marketplace.data['producers_products'][self.producer_id])

    # test order
    def test_place_order(self):
        """ Test order """
        product_dict1 = self.get_product_dict()
        product1 = str(product_dict1)
        # publish it
        self.marketplace.publish(self.producer_id, product1)
        # second asset
        product_dict2 = {
            "product_type": "Tea",
            "name": "Raspberry",
            "type": "Red",
            "price": 10
        }
        # publish it
        product2 = str(product_dict2)
        self.marketplace.publish(self.producer_id, product2)
        # new_cart & add both to the consumer cart
        cart_id = self.marketplace.new_cart()
        self.marketplace.add_to_cart(cart_id, product1)
        self.marketplace.add_to_cart(cart_id, product2)
        # place the order
        order = self.marketplace.place_order(cart_id)
        # check correct number of products 
        # check that the products are corect & prod removed from customer cart
        self.assertEqual(len(order), 2)
        self.assertIn(product1, order)
        self.assertIn(product2, order)
        self.assertEqual(len(self.marketplace.data['consumers_carts'][cart_id]), 0)
