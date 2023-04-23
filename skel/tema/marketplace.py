from threading import Lock
import logging
import unittest

class Marketplace:
    
    def __init__(self, queue_size_per_producer):

        self.queue_size_per_producer = queue_size_per_producer

        #Creem lock-urile pentru a putea lucra thread safe cu comenzile, 
        #producatorii si operatiile de aprovizionare de stock sau cumparare
        self.lock_order = Lock()
        self.lock_cart = Lock()
        self.lock_producer = Lock()

        self.identifier_cart = 0
        self.identifier_producer = 0

        #Creem configurarile pentru afisarea logg-urilor in fisierul maketplace.log
        logging.basicConfig(
            level=logging.DEBUG,
            handlers=[
                logging.FileHandler('marketplace.log', mode='w'),
            ],
            format='[%(asctime)s] - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        self.logger = logging.getLogger(__name__)

        #Initializam un dictionar pentru a tine evidenta produselor existente pe categorii
        self.database = {}
        for key in ['reserved_products', 'marketplace_products', 'available_products']:
            self.database[key] = {}

    def register_producer(self):

        #Deschidem lock-ul pentru a proteja urmatoarera zona de cod
        self.lock_producer.acquire()
        #Obtinem urmatorul id pentru producator, apoi il asignam in dictionar cu
        #o lista goala
        self.identifier_producer = self.identifier_producer + 1
        identifier_producer = self.identifier_producer - 1
        self.logger.info("Operation Accepted: Succesfully registered producer with id: %s", identifier_producer)
        self.database['available_products'][identifier_producer] = []
        self.lock_producer.release()
        return identifier_producer

    def publish(self, identifier_producer, product):

        #Cand un produs este publicat, acesta ajunge atat ca fiind valabil pentru cumparare
        #dar este si contorizat in marketplace. Astfel, produsul este pus in dictionar corespunzator
        self.logger.info("Operation Accepted: Product %s was succesfully published by producer with id %d", product.__str__(), identifier_producer)
        self.database['available_products'][identifier_producer].append(product)
        self.database['marketplace_products'][product] = identifier_producer
        return True

    def new_cart(self):

        #Deschidem lock-ul pentru a proteja urmatoarera zona de cod
        self.lock_cart.acquire()
        #Odata ce un nou cart se creaza, instantiem o noua lista goala 
        #in dictionar pentru a putea in viitor sa adaugam noi produse
        self.logger.info("Operation Accepted: Sucessfully created cart with id: %d", self.identifier_cart)
        self.database['reserved_products'][self.identifier_cart] = []
        self.identifier_cart = self.identifier_cart + 1
        self.lock_cart.release()
        return self.identifier_cart - 1

    def add_to_cart(self, identifier_cart, product):

        try:
            # I used the next function to find the id for the product
            id_producer = next((i for i in range(self.identifier_producer)
                                if product in self.database['available_products'][i]), None)
            # If prod is available -> add to cart and put log message
            if id_producer is not None:
                self.database['reserved_products'][identifier_cart].append(product)
                self.database['available_products'][id_producer].remove(product)

                self.logger.info(f"Succesfully added a new product to the cart {identifier_cart}: {product}")
                self.logger.info(f"Succesfully removed a product from producer {id_producer}: {product}")

                return True
            return False
        except Exception as exc_catch:
            self.logger.error("Error adding product to cart: %s", str(exc_catch))
            return False

    def remove_from_cart(self, identifier_cart, product):

        try:
            # if prod is in cart
            if product in self.database['reserved_products'][identifier_cart]:
                # get id prod from all products of the prod
                identifier_producer = self.database['marketplace_products'][product]
                # add prod to producer list & remove from cart
                self.database['available_products'][identifier_producer].append(product)
                self.database['reserved_products'][identifier_cart].remove(product)

                self.logger.info(
                    "Succesfully removed product %s from cart %d", product.__str__(), identifier_cart)
        except Exception as exc_catch:
            self.logger.error("Error removing product from cart: %s", str(exc_catch))

    def place_order(self, identifier_cart):

        with self.lock_order:
            try:
                # copy the products from cart
                order = self.database['reserved_products'][identifier_cart].copy()
                # clear the cart
                self.database['reserved_products'][identifier_cart].clear()
                # return order with the content of the cart
                self.logger.info(
                    "The order placed %s from cart with id: %d", order.__str__(), identifier_cart)
                return order
            except Exception as exc_catch:
                self.logger.error("Error placing order: %s", str(exc_catch))
                return []


#Tests for Marketplace flow

class TestMarketplace(unittest.TestCase):

    def setUp(self):
        # initialise setup for testing
        self.marketplace = Marketplace(10)
        self.identifier_producer = self.marketplace.register_producer()

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
        identifier_producer = self.marketplace.register_producer()
        self.assertEqual(identifier_producer, 1)

    def test_publish(self):
        """ Test publish """
        product_dict = self.get_product_dict()
        product = str(product_dict)
        # publish product
        result = self.marketplace.publish(self.identifier_producer, product)
        # if true => ensures that the product was published
        self.assertTrue(result)
        # makes sure that product was added to the list
        self.assertIn(product, self.marketplace.database['available_products'][self.identifier_producer])
        # makes sure that all products dict is up with new product
        self.assertEqual(self.marketplace.database['marketplace_products'][product], self.identifier_producer)

    def test_new_cart(self):
        """ Test new_cart """
        identifier_cart = self.marketplace.new_cart()
        # makes sure that new_cart is correctly init a new cart
        self.assertEqual(identifier_cart, 0)

    # test add
    def test_add_to_cart(self):
        """ Test add_to_cart """
        product_dict = self.get_product_dict()
        product = str(product_dict)
        # check if it published before adding to cart
        self.marketplace.publish(self.identifier_producer, product)

        identifier_cart = self.marketplace.new_cart()
        result = self.marketplace.add_to_cart(identifier_cart, product)
        # check if it is added to cart & add to correct cart & 
        # removed from the list of products by the prod
        self.assertTrue(result)
        self.assertIn(product, self.marketplace.database['reserved_products'][identifier_cart])
        self.assertNotIn(product, self.marketplace.database['available_products'][self.identifier_producer])

    # test remove
    def test_remove_from_cart(self):
        """ Test remove """
        product_dict = self.get_product_dict()
        product = str(product_dict)
        # check if published
        self.marketplace.publish(self.identifier_producer, product)
        # add to the cart
        identifier_cart = self.marketplace.new_cart()
        self.marketplace.add_to_cart(identifier_cart, product)
        # remove from cart -> add back to the list of published
        self.marketplace.remove_from_cart(identifier_cart, product)
        # check if removed & added back to list of prod
        self.assertNotIn(product, self.marketplace.database['reserved_products'][identifier_cart])
        self.assertIn(product, self.marketplace.database['available_products'][self.identifier_producer])

    # test order
    def test_place_order(self):
        """ Test order """
        product_dict1 = self.get_product_dict()
        product1 = str(product_dict1)
        # publish it
        self.marketplace.publish(self.identifier_producer, product1)
        # second asset
        product_dict2 = {
            "product_type": "Tea",
            "name": "Raspberry",
            "type": "Red",
            "price": 10
        }
        # publish it
        product2 = str(product_dict2)
        self.marketplace.publish(self.identifier_producer, product2)
        # new_cart & add both to the consumer cart
        identifier_cart = self.marketplace.new_cart()
        self.marketplace.add_to_cart(identifier_cart, product1)
        self.marketplace.add_to_cart(identifier_cart, product2)
        # place the order
        order = self.marketplace.place_order(identifier_cart)
        # check correct number of products 
        # check that the products are corect & prod removed from customer cart
        self.assertEqual(len(order), 2)
        self.assertIn(product1, order)
        self.assertIn(product2, order)
        self.assertEqual(len(self.marketplace.database['reserved_products'][identifier_cart]), 0)
