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
            #Pentru a putea adauga un produs in cos, acesta trebuie sa se afle
            #in lista de produse valabile.
            identifier_producer = -1
            for i in range(self.identifier_producer):
                if product in self.database['available_products'][i]:
                    identifier_producer = i
                    break
            #Daca produsul este valabil, il adaugam in lista de produse
            #rezervate si il scoatem din cea de produse valabile
            if identifier_producer >= 0:
                available_products = self.database['available_products'][identifier_producer]
                reserved_products = self.database['reserved_products'][identifier_cart]
                available_products.remove(product)
                reserved_products.append(product)
                self.logger.info("Operation Accepted: Succesfully removed product %s from producer with id %d", product.__str__(), identifier_producer)
                self.logger.info("Operation Accepted: Succesfully added product %s in cart with id %d", product.__str__(), identifier_cart)
                return True
            return False
        except Exception as thrown_exception:
            self.logger.error("Operation Rejected: Error adding product to cart: %s", thrown_exception.__str__())
            return False

    def remove_from_cart(self, identifier_cart, product):

        #Daca produsul se afla in lista de produse a cosului dat ca
        #parametru, este scos si adaugat in lista de produse valabile din marketplace
        cart_products = self.database['reserved_products'].get(identifier_cart, [])
        if product in cart_products:
            producer = self.database['marketplace_products'].get(product)
            if producer is not None:
                available_products = self.database['available_products'].get(producer, [])
                available_products.append(product)
                self.database['available_products'][producer] = available_products
                reserved_products = self.database['reserved_products'].get(identifier_cart, [])
                reserved_products.remove(product)
                self.database['reserved_products'][identifier_cart] = reserved_products

    def place_order(self, identifier_cart):

        #Deschidem lock-ul pentru a proteja urmatoarera zona de cod
        self.lock_order.acquire()
        reserved_products = self.database.get('reserved_products', {})
        cart_products = reserved_products.get(identifier_cart, [])
        order_to_place = list(cart_products)
        reserved_products[identifier_cart] = []
        self.database['reserved_products'] = reserved_products
        self.logger.info("Operation Accepted: Succesfully placed order %s from cart with id %d", order_to_place.__str__(), identifier_cart)
        self.lock_order.release()
        return order_to_place


#Tests for Marketplace flow

class TestMarketplace(unittest.TestCase):
    def setUp(self):
        self.marketplace = Marketplace(5)

    def test_register_producer(self):
        producer_id = self.marketplace.register_producer()
        self.assertEqual(producer_id, 1)

        producer_id_2 = self.marketplace.register_producer()
        self.assertEqual(producer_id_2, 2)

    def test_publish(self):
        producer_id = self.marketplace.register_producer()
        product = Product('product', 10)

        self.assertTrue(self.marketplace.publish(producer_id, product))
        self.assertEqual(len(self.marketplace.database['available_products'][producer_id]), 1)

        self.assertFalse(self.marketplace.publish(producer_id, product))
        self.assertEqual(len(self.marketplace.database['available_products'][producer_id]), 1)

    def test_new_cart(self):
        cart_id = self.marketplace.new_cart()
        self.assertEqual(cart_id, 0)

        cart_id_2 = self.marketplace.new_cart()
        self.assertEqual(cart_id_2, 1)

    def test_add_to_cart(self):
        producer_id = self.marketplace.register_producer()
        product = Product('product', 10)

        cart_id = self.marketplace.new_cart()
        self.assertTrue(self.marketplace.add_to_cart(cart_id, product))
        self.assertEqual(len(self.marketplace.database['reserved_products'][cart_id]), 1)

        self.assertFalse(self.marketplace.add_to_cart(cart_id, product))
        self.assertEqual(len(self.marketplace.database['reserved_products'][cart_id]), 1)

        product_2 = Product('product_2', 20)
        self.assertFalse(self.marketplace.add_to_cart(cart_id, product_2))
        self.assertEqual(len(self.marketplace.database['reserved_products'][cart_id]), 1)

    def test_remove_from_cart(self):
        producer_id = self.marketplace.register_producer()
        product = Product('product', 10)

        cart_id = self.marketplace.new_cart()
        self.marketplace.add_to_cart(cart_id, product)
        self.marketplace.remove_from_cart(cart_id, product)
        self.assertEqual(len(self.marketplace.database['reserved_products'][cart_id]), 0)
        self.assertEqual(len(self.marketplace.database['available_products'][producer_id]), 1)

        self.marketplace.remove_from_cart(cart_id, product)
        self.assertEqual(len(self.marketplace.database['reserved_products'][cart_id]), 0)
        self.assertEqual(len(self.marketplace.database['available_products'][producer_id]), 1)

    def test_place_order(self):
        producer_id = self.marketplace.register_producer()
        product = Product('product', 10)

        cart_id = self.marketplace.new_cart()
        self.marketplace.add_to_cart(cart_id, product)
        order = self.marketplace.place_order(cart_id)
        self.assertEqual(order, [product])
        self.assertEqual(len(self.marketplace.database['reserved_products'][cart_id]), 0)

        cart_id_2 = self.marketplace.new_cart()
