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

        # Inregistram un nou producator in marketplace
        identifier_producer = self.marketplace.register_producer()
        while True:
            #Parcurgem toate produsele ce vor fi puse pe piata de
            #producatorul curent si incercam sa le punem.
            for current_product in self.products:
                identifier_product = current_product[0]
                quantity = current_product[1]
                wait_time = current_product[2]
                products_to_add = quantity
                while True:
                    if products_to_add == 0:
                        break
                    products_to_add -= 1
                    #Daca produsul este acceptat vom astepta un timp predefinit
                    #produs de aceasta operatiune, daca nu, asteptam sa incercam din nou
                    if self.marketplace.publish(identifier_producer, identifier_product):
                        sleep(wait_time)
                    else:
                        sleep(self.republish_wait_time)
                        break
