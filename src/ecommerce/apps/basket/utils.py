from oscar.apps.basket.utils import BasketMessageGenerator, LineOfferConsumer


class BasketMessageGenerator(BasketMessageGenerator):
    new_total_template_name = 'eta/basket/messages/new_total.html'
    offer_lost_template_name = 'eta/basket/messages/offer_lost.html'
    offer_gained_template_name = 'eta/basket/messages/offer_gained.html'


class LineOfferConsumer(LineOfferConsumer):
    pass
