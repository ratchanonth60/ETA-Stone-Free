from django.urls import reverse
from oscar.apps.catalogue.reviews.signals import review_added
from oscar.test.contextmanagers import mock_signal_receiver

from ecommerce.apps.catalogue.reviews.models import ProductReview, Vote
from ecommerce.test.factories import UserFactory, create_product
from ecommerce.test.testcases import TestCase, WebTestCase


class TestACustomer(WebTestCase):

    def setUp(self):
        self.product = create_product()

    def test_reviews_list_sorting_form(self):
        reviews_page = self.app.get(reverse(
            'catalogue:reviews-list',
            kwargs={'product_slug': self.product.slug, 'product_pk': self.product.id}
        ))
        self.assertFalse(reviews_page.context['form'].errors)

    def test_can_add_a_review_when_anonymous(self):
        detail_page = self.app.get(self.product.get_absolute_url())
        add_review_page = detail_page.click(linkid='write_review')
        form = add_review_page.forms['add_review_form']
        form['title'] = 'This is great!'
        form['score'] = 5
        form['body'] = 'Loving it, loving it, loving it'
        form['name'] = 'John Doe'
        form['email'] = 'john@example.com'
        form.submit()

        self.assertEqual(1, self.product.reviews.all().count())

    def test_can_add_a_review_when_signed_in(self):
        user = UserFactory()
        detail_page = self.app.get(self.product.get_absolute_url(),
                                   user=user)
        add_review_page = detail_page.click(linkid="write_review")
        form = add_review_page.forms['add_review_form']
        form['title'] = 'This is great!'
        form['score'] = 5
        form['body'] = 'Loving it, loving it, loving it'
        form.submit()

        self.assertEqual(1, self.product.reviews.all().count())

    def test_adding_a_review_sends_a_signal(self):
        review_user = UserFactory()
        detail_page = self.app.get(self.product.get_absolute_url(),
                                   user=review_user)
        with mock_signal_receiver(review_added) as receiver:
            add_review_page = detail_page.click(linkid="write_review")
            form = add_review_page.forms['add_review_form']
            form['title'] = 'This is great!'
            form['score'] = 5
            form['body'] = 'Loving it, loving it, loving it'
            form.submit()
            self.assertEqual(receiver.call_count, 1)
        self.assertEqual(1, self.product.reviews.all().count())


class TestAddVoteView(TestCase):
    def setUp(self):
        self.client.force_login(UserFactory())

    def test_voting_on_product_review_returns_404_on_non_public_product(self):
        product = create_product(is_public=False)
        review = ProductReview.objects.create(
            product=product,
            **{
                "title": "Awesome!",
                "score": 5,
                "body": "Wonderful product",
            }
        )
        path = reverse(
            "catalogue:reviews-vote",
            kwargs={
                "product_slug": product.slug,
                "product_pk": product.pk,
                "pk": review.pk,
            },
        )

        response = self.client.post(path, data={"delta": Vote.UP})

        self.assertEqual(response.status_code, 404)

    def test_voting_on_product_review_redirect_on_public_product(self):
        product = create_product(is_public=True)
        review = ProductReview.objects.create(
            product=product,
            **{
                "title": "Awesome!",
                "score": 5,
                "body": "Wonderful product",
            }
        )
        path = reverse(
            "catalogue:reviews-vote",
            kwargs={
                "product_slug": product.slug,
                "product_pk": product.pk,
                "pk": review.pk,
            },
        )

        response = self.client.post(path, data={"delta": Vote.UP})

        self.assertRedirects(response, product.get_absolute_url())

    def test_creating_product_review_returns_404_on_non_public_product(self):
        product = create_product(is_public=False)
        path = reverse(
            "catalogue:reviews-add",
            kwargs={"product_slug": product.slug, "product_pk": product.pk},
        )

        response = self.client.post(
            path,
            data={
                "title": "Awesome!",
                "score": 5,
                "body": "Wonderful product",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_creating_product_review_redirect_on_public_product(self):
        product = create_product(is_public=True)
        path = reverse(
            "catalogue:reviews-add",
            kwargs={"product_slug": product.slug, "product_pk": product.pk},
        )

        response = self.client.post(
            path,
            data={
                "title": "Awesome!",
                "score": 5,
                "body": "Wonderful product",
            },
        )

        self.assertRedirects(response, product.get_absolute_url())


class TestProductReviewList(TestCase):
    def setUp(self):
        self.client.force_login(UserFactory())

    def test_listing_product_reviews_returns_404_on_non_public_product(self):
        product = create_product(is_public=False)
        path = reverse(
            "catalogue:reviews-list",
            kwargs={"product_slug": product.slug, "product_pk": product.pk},
        )

        response = self.client.get(path)

        self.assertEqual(response.status_code, 404)

    def test_listing_product_reviews_returns_200_on_public_product(self):
        product = create_product(is_public=True)
        path = reverse(
            "catalogue:reviews-list",
            kwargs={"product_slug": product.slug, "product_pk": product.pk},
        )

        response = self.client.get(path)

        self.assertEqual(response.status_code, 200)


class TestProductReviewDetail(TestCase):
    def setUp(self):
        self.client.force_login(UserFactory())

    def test_retrieving_product_review_returns_404_on_non_public_product(self):
        product = create_product(is_public=False)
        review = ProductReview.objects.create(
            product=product,
            **{
                "title": "Awesome!",
                "score": 5,
                "body": "Wonderful product",
            }
        )
        path = reverse(
            "catalogue:reviews-detail",
            kwargs={
                "product_slug": product.slug,
                "product_pk": product.pk,
                "pk": review.pk,
            },
        )

        response = self.client.get(path)

        self.assertEqual(response.status_code, 404)

    def test_retrieving_product_review_returns_200_on_public_product(self):
        product = create_product(is_public=True)
        review = ProductReview.objects.create(
            product=product,
            **{
                "title": "Awesome!",
                "score": 5,
                "body": "Wonderful product",
            }
        )
        path = reverse(
            "catalogue:reviews-detail",
            kwargs={
                "product_slug": product.slug,
                "product_pk": product.pk,
                "pk": review.pk,
            },
        )

        response = self.client.get(path)

        self.assertEqual(response.status_code, 200)
