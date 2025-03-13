from django.contrib.messages import get_messages
from django.urls import reverse

from ecommerce.apps.dashboard.vouchers import views
from ecommerce.apps.offer.models import ConditionalOffer
from ecommerce.apps.voucher.models import Voucher, VoucherSet
from ecommerce.test.factories import voucher
from ecommerce.test.factories.offer import ConditionalOfferFactory
from ecommerce.test.fixtures import RequestFactory
from ecommerce.test.testcases import TestCase, WebTestCase


class TestVoucherListSearch(WebTestCase):
    is_staff = True

    TEST_CASES = [
        ({}, ['Not in a set']),
        (
            {'name': 'Bob Smith'},
            ['Name matches "Bob Smith"']
        ),
        (
            {'code': 'abcd1234'},
            ['Code is "ABCD1234"']
        ),
        (
            {'offer_name': 'Shipping offer'},
            ['Offer name matches "Shipping offer"']
        ),
        (
            {'is_active': True},
            ['Is active']
        ),
        (
            {'is_active': False},
            ['Is inactive']
        ),
        (
            {'in_set': True},
            ['In a set']
        ),
        (
            {'in_set': False},
            ['Not in a set']
        ),
        (
            {'has_offers': True},
            ['Has offers']
        ),
        (
            {'has_offers': False},
            ['Has no offers']
        ),
        (
            {
                'name': 'Bob Smith',
                'code': 'abcd1234',
                'offer_name': 'Shipping offer',
                'is_active': True,
                'in_set': True,
                'has_offers': True,
            },
            [
                'Name matches "Bob Smith"',
                'Code is "ABCD1234"',
                'Offer name matches "Shipping offer"',
                'Is active',
                'In a set',
                'Has offers',
            ]
        ),
    ]

    def test_search_filter_descriptions(self):
        url = reverse('dashboard:voucher-list')
        for params, expected_filters in self.TEST_CASES:
            response = self.get(url, params=params)
            self.assertEqual(response.status_code, 200)
            applied_filters = [
                el.text.strip() for el in
                response.html.select('.search-filter-list .badge')
            ]
            self.assertEqual(applied_filters, expected_filters)


class TestDashboardVouchers(TestCase):

    def test_voucher_update_view_for_voucher_in_set(self):
        vs = voucher.VoucherSetFactory(count=10)
        v = vs.vouchers.first()

        view = views.VoucherUpdateView.as_view()

        request = RequestFactory().get('/')
        response = view(request, pk=v.pk)
        assert response.status_code == 302
        assert response.url == reverse('dashboard:voucher-set-update', kwargs={'pk': vs.pk})
        assert [(m.level_tag, str(m.message)) for m in get_messages(request)][0] == (
            'warning', "The voucher can only be edited as part of its set")

        data = {
            'code': v.code,
            'name': "New name",
            'start_datetime': v.start_datetime,
            'end_datetime': v.end_datetime,
            'usage': v.usage,
            'offers': [v.offers],
        }
        request = RequestFactory().post('/', data=data)
        response = view(request, pk=v.pk)
        assert response.status_code == 302
        assert response.url == reverse('dashboard:voucher-set-update', kwargs={'pk': vs.pk})
        assert [(m.level_tag, str(m.message)) for m in get_messages(request)][0] == (
            'warning', "The voucher can only be edited as part of its set")
        v.refresh_from_db()
        assert v.name != "New name"

    def test_voucher_delete_view(self):
        v = voucher.VoucherFactory()
        v.offers.add(ConditionalOfferFactory(offer_type=ConditionalOffer.VOUCHER))
        assert Voucher.objects.count() == 1
        assert ConditionalOffer.objects.count() == 1
        request = RequestFactory().post('/')
        response = views.VoucherDeleteView.as_view()(request, pk=v.pk)
        assert Voucher.objects.count() == 0
        # Related offer is not deleted
        assert ConditionalOffer.objects.count() == 1
        assert response.status_code == 302
        assert response.url == reverse('dashboard:voucher-list')
        assert [(m.level_tag, str(m.message)) for m in get_messages(request)][0] == ('warning', "Voucher deleted")

    def test_voucher_delete_view_for_voucher_in_set(self):
        vs = voucher.VoucherSetFactory(count=10)
        assert Voucher.objects.count() == 10
        request = RequestFactory().post('/')
        response = views.VoucherDeleteView.as_view()(request, pk=vs.vouchers.first().pk)
        vs.refresh_from_db()
        assert vs.count == 9  # "count" is updated
        assert Voucher.objects.count() == 9
        assert response.status_code == 302
        assert response.url == reverse('dashboard:voucher-set-detail', kwargs={'pk': vs.pk})
        assert [(m.level_tag, str(m.message)) for m in get_messages(request)][0] == ('warning', "Voucher deleted")


class TestDashboardVoucherSets(TestCase):

    def test_voucher_set_list_view(self):
        voucher.VoucherSetFactory.create_batch(30)
        view = views.VoucherSetListView.as_view()
        request = RequestFactory().get('/')
        response = view(request)
        # if these are missing the pagination is broken
        assert response.context_data['paginator']
        assert response.context_data['page_obj']
        assert response.status_code == 200

    def test_voucher_set_detail_view(self):
        voucher.VoucherSetFactory(count=10)
        vs2 = voucher.VoucherSetFactory(count=15)
        request = RequestFactory().get('/')
        response = views.VoucherSetDetailView.as_view()(request, pk=vs2.pk)
        # The view should only list vouchers for vs2
        assert len(response.context_data['vouchers']) == 15
        assert response.status_code == 200

    def test_voucher_set_delete_view(self):
        vs = voucher.VoucherSetFactory(count=10)
        assert VoucherSet.objects.count() == 1
        assert Voucher.objects.count() == 10
        request = RequestFactory().post('/')
        response = views.VoucherSetDeleteView.as_view()(request, pk=vs.pk)
        assert VoucherSet.objects.count() == 0
        assert Voucher.objects.count() == 0
        assert response.status_code == 302
        assert response.url == reverse('dashboard:voucher-set-list')
        assert [(m.level_tag, str(m.message)) for m in get_messages(request)][0] == ('warning', "Voucher set deleted")
