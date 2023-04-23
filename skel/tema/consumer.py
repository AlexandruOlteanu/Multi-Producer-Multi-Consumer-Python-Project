from threading import Thread
from time import sleep

class Consumer(Thread):

    def __init__(self, carts, marketplace, retry_wait_time, **kwargs):

        Thread.__init__(self, **kwargs)
        self.kwargs = kwargs
        self.carts = carts
        self.marketplace = marketplace
        self.retry_wait_time = retry_wait_time

    def run(self):
        def add_to_cart(product, quantity, identifier_cart):
            # Cand un consumator doreste sa adauge un produs in cos, se face o verificare
            # in marketplace daca avem un produs valabil de acest tip, daca da, automat
            # se rezerva produsul si este adaugat in cart. Daca nu, se asteapta un timp
            # pentru ca produsul sa poata redeveni disponibil. In momentul in care au fost
            # adaugate in cart toate produsele de acest timp, se continua procesul
            added_products = 0
            while True:
                available_product = self.marketplace.add_to_cart(identifier_cart, product)
                if available_product is False:
                    sleep(self.retry_wait_time)
                else:
                    added_products += 1
                if added_products == quantity:
                    break

        # Cat timp inca avem produse ce trebuie scoase din cos, se va apela
        # functia de remove_from_cart din clasa Marketplace
        def remove_from_cart(product, quantity, identifier_cart):
            products_to_delete = quantity
            while True:
                if products_to_delete == 0:
                    break
                products_to_delete -= 1
                self.marketplace.remove_from_cart(identifier_cart, product)

        result = []

        # Parcurgem fiecare cart din input
        for current_cart in self.carts:
            # Creem acest nou cart, fiind valabil pentru adaugare si scoatere de produse
            identifier_cart = self.marketplace.new_cart()
            # Realizam actiunile de add sau remove pentru produsele dorite
            for action in current_cart:
                apply_function = action["type"]
                product = action["product"]
                quantity = action["quantity"]
                if apply_function == "remove":
                    remove_from_cart(product, quantity, identifier_cart)
                else:
                    add_to_cart(product, quantity, identifier_cart)
            # Odata finalizat state-ul final al cart-ului, plasam comanda
            # si afisam produsele finale ce au fost cumparate
            products_bought = self.marketplace.place_order(identifier_cart)
            result.extend(list(map(lambda product: f"{self.name} bought {product}", products_bought)))

        final_result = "\n".join(result)

        with self.marketplace.lock_order:
            print(final_result)
