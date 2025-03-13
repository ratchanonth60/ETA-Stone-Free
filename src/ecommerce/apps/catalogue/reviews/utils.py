from django.conf import settings

from oscar.core.loading import get_model


def get_default_review_status():
    product_review = get_model('reviews', 'ProductReview')

    if settings.OSCAR_MODERATE_REVIEWS:
        return product_review.FOR_MODERATION

    return product_review.APPROVED
