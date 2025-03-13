import json

from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from oscar.apps.offer.custom import create_benefit, create_condition
from oscar.core.loading import get_model

from ecommerce.apps.dashboard.offers import views as offer_views
from ecommerce.apps.offer import models
from ecommerce.test import factories
from ecommerce.test.factories.offer import ConditionalOfferFactory, RangeFactory
from ecommerce.test.fixtures import RequestFactory
from ecommerce.test.model_tests_app.models import CustomBenefitModel
from ecommerce.test.testcases import TestCase, WebTestCase

Range = get_model('offer', 'Range')
ConditionalOffer = get_model('offer', 'ConditionalOffer')
Benefit = get_model('offer', 'Benefit')
Condition = get_model('offer', 'Condition')


class TestCreateOfferWizardStepView(TestCase):

    def setUp(self):
        range_ = RangeFactory()

        self.metadata_form_kwargs_session_data = {
            'data': {
                'name': 'Test offer',
                'slug': '',
                'description': 'Test description',
                'offer_type': ConditionalOffer.SITE,
                'exclusive': True,
                'status': ConditionalOffer.OPEN,
                'condition': None,
                'benefit': None,
                'priority': 0,
                'start_datetime': None,
                'end_datetime': None,
                'max_global_applications': None,
                'max_user_applications': None,
                'max_basket_applications': None,
                'max_discount': None,
                'total_discount': '0.00',
                'num_applications': 0,
                'num_orders': 0,
                'redirect_url': '',
                'date_created': None,
            },
        }
        self.metadata_obj_session_data = [{
            'model': 'offer.conditionaloffer',
            'pk': None,
            'fields': {
                'name': 'Test offer',
                'description': 'Test description',
                'offer_type': ConditionalOffer.SITE,
            },
        }]
        self.benefit_form_kwargs_session_data = {
            'data': {
                'range': range_.pk,
                'type': Benefit.PERCENTAGE,
                'value': '10',
                'max_affected_items': None,
                'custom_benefit': '',
            },
        }
        self.benefit_obj_session_data = [{
            'model': 'offer.benefit',
            'pk': None,
            'fields': {
                'range': range_.pk,
                'type': Benefit.PERCENTAGE,
                'value': '10',
                'max_affected_items': None,
                'proxy_class': None,
            },
        }]
        self.condition_form_kwargs_session_data = {
            'data': {
                'range': range_.pk,
                'type': Condition.COUNT,
                'value': '10',
                'custom_condition': '',
            },
        }
        self.condition_obj_session_data = [{
            'model': 'offer.condition',
            'pk': None,
            'fields': {
                'range': range_.pk,
                'type': Condition.COUNT,
                'value': '10',
                'proxy_class': None,
            },
        }]

    def test_offer_meta_data_view(self):
        request = RequestFactory().post('/', data={
            'name': 'Test offer',
            'description': 'Test description',
            'offer_type': ConditionalOffer.SITE,
        })
        response = offer_views.OfferMetaDataView.as_view()(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:offer-benefit'))
        self.assertJSONEqual(request.session['offer_wizard']['metadata'], {
            'data': {
                'name': 'Test offer',
                'description': 'Test description',
                'offer_type': ConditionalOffer.SITE,
            },
        })
        self.assertJSONEqual(request.session['offer_wizard']['metadata_obj'], [{
            'model': 'offer.conditionaloffer',
            'pk': None,
            'fields': {
                'name': 'Test offer',
                'slug': '',
                'description': 'Test description',
                'offer_type': ConditionalOffer.SITE,
                'exclusive': True,
                'status': ConditionalOffer.OPEN,
                'condition': None,
                'benefit': None,
                'priority': 0,
                'start_datetime': None,
                'end_datetime': None,
                'max_global_applications': None,
                'max_user_applications': None,
                'max_basket_applications': None,
                'max_discount': None,
                'total_discount': '0.00',
                'num_applications': 0,
                'num_orders': 0,
                'redirect_url': '',
                'date_created': None,
            },
        }])

    def test_offer_benefit_view_with_built_in_benefit_type(self):
        range_ = RangeFactory()

        request = RequestFactory().post('/', data={
            'range': range_.pk,
            'type': Benefit.PERCENTAGE,
            'value': 10,
        })
        request.session['offer_wizard'] = {
            'metadata': json.dumps(self.metadata_form_kwargs_session_data),
            'metadata_obj': json.dumps(self.metadata_obj_session_data),
        }
        response = offer_views.OfferBenefitView.as_view()(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:offer-condition'))
        self.assertJSONEqual(request.session['offer_wizard']['metadata'], self.metadata_form_kwargs_session_data)
        self.assertJSONEqual(request.session['offer_wizard']['metadata_obj'], self.metadata_obj_session_data)
        self.assertJSONEqual(request.session['offer_wizard']['benefit'], {
            'data': {
                'range': range_.pk,
                'type': Benefit.PERCENTAGE,
                'value': '10',
                'max_affected_items': None,
                'custom_benefit': '',
            },
        })
        self.assertJSONEqual(request.session['offer_wizard']['benefit_obj'], [{
            'model': 'offer.benefit',
            'pk': None,
            'fields': {
                'range': range_.pk,
                'type': Benefit.PERCENTAGE,
                'value': '10',
                'max_affected_items': None,
                'proxy_class': None,
            },
        }])

    def test_offer_benefit_view_with_custom_benefit_type(self):
        benefit = create_benefit(CustomBenefitModel)

        request = RequestFactory().post('/', data={
            'custom_benefit': benefit.pk,
        })
        request.session['offer_wizard'] = {
            'metadata': json.dumps(self.metadata_form_kwargs_session_data),
            'metadata_obj': json.dumps(self.metadata_obj_session_data),
        }
        response = offer_views.OfferBenefitView.as_view()(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:offer-condition'))
        self.assertJSONEqual(request.session['offer_wizard']['metadata'], self.metadata_form_kwargs_session_data)
        self.assertJSONEqual(request.session['offer_wizard']['metadata_obj'], self.metadata_obj_session_data)
        self.assertJSONEqual(request.session['offer_wizard']['benefit'], {
            'data': {
                'range': None,
                'type': '',
                'value': None,
                'max_affected_items': None,
                'custom_benefit': str(benefit.pk),
            },
        })
        self.assertJSONEqual(request.session['offer_wizard']['benefit_obj'], [{
            'model': 'offer.benefit',
            'pk': benefit.pk,
            'fields': {
                'range': None,
                'type': '',
                'value': None,
                'max_affected_items': None,
                'proxy_class': benefit.proxy_class,
            }
        }])

    def test_offer_condition_view_with_built_in_condition_type(self):
        range_ = RangeFactory()

        request = RequestFactory().post('/', data={
            'range': range_.pk,
            'type': Condition.COUNT,
            'value': 10,
        })
        request.session['offer_wizard'] = {
            'metadata': json.dumps(self.metadata_form_kwargs_session_data),
            'metadata_obj': json.dumps(self.metadata_obj_session_data),
            'benefit': json.dumps(self.benefit_form_kwargs_session_data),
            'benefit_obj': json.dumps(self.benefit_obj_session_data),
        }
        response = offer_views.OfferConditionView.as_view()(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:offer-restrictions'))
        self.assertJSONEqual(request.session['offer_wizard']['metadata'], self.metadata_form_kwargs_session_data)
        self.assertJSONEqual(request.session['offer_wizard']['metadata_obj'], self.metadata_obj_session_data)
        self.assertJSONEqual(request.session['offer_wizard']['benefit'], self.benefit_form_kwargs_session_data)
        self.assertJSONEqual(request.session['offer_wizard']['benefit_obj'], self.benefit_obj_session_data)
        self.assertJSONEqual(request.session['offer_wizard']['condition'], {
            'data': {
                'range': range_.pk,
                'type': Condition.COUNT,
                'value': '10',
                'custom_condition': '',
            },
        })
        self.assertJSONEqual(request.session['offer_wizard']['condition_obj'], [{
            'model': 'offer.condition',
            'pk': None,
            'fields': {
                'range': range_.pk,
                'type': Condition.COUNT,
                'value': '10',
                'proxy_class': None,
            },
        }])

    def test_offer_condition_view_with_custom_condition_type(self):
        condition = create_condition(Condition)

        request = RequestFactory().post('/', data={
            'custom_condition': condition.pk,
        })
        request.session['offer_wizard'] = {
            'metadata': json.dumps(self.metadata_form_kwargs_session_data),
            'metadata_obj': json.dumps(self.metadata_obj_session_data),
            'benefit': json.dumps(self.benefit_form_kwargs_session_data),
            'benefit_obj': json.dumps(self.benefit_obj_session_data),
        }
        response = offer_views.OfferConditionView.as_view()(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:offer-restrictions'))
        self.assertJSONEqual(request.session['offer_wizard']['metadata'], self.metadata_form_kwargs_session_data)
        self.assertJSONEqual(request.session['offer_wizard']['metadata_obj'], self.metadata_obj_session_data)
        self.assertJSONEqual(request.session['offer_wizard']['benefit'], self.benefit_form_kwargs_session_data)
        self.assertJSONEqual(request.session['offer_wizard']['benefit_obj'], self.benefit_obj_session_data)
        self.assertJSONEqual(request.session['offer_wizard']['condition'], {
            'data': {
                'range': None,
                'type': '',
                'value': None,
                'custom_condition': str(condition.pk),
            },
        })
        self.assertJSONEqual(request.session['offer_wizard']['condition_obj'], [{
            'model': 'offer.condition',
            'pk': condition.pk,
            'fields': {
                'range': None,
                'type': '',
                'value': None,
                'proxy_class': condition.proxy_class,
            }
        }])

    def test_offer_restrictions_view(self):
        request = RequestFactory().post('/', data={
            'priority': 0,
        })
        request.session['offer_wizard'] = {
            'metadata': json.dumps(self.metadata_form_kwargs_session_data),
            'metadata_obj': json.dumps(self.metadata_obj_session_data),
            'benefit': json.dumps(self.benefit_form_kwargs_session_data),
            'benefit_obj': json.dumps(self.benefit_obj_session_data),
            'condition': json.dumps(self.condition_form_kwargs_session_data),
            'condition_obj': json.dumps(self.condition_obj_session_data),
        }
        response = offer_views.OfferRestrictionsView.as_view()(request)

        offer = ConditionalOffer.objects.get()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:offer-detail', kwargs={'pk': offer.pk}))
        self.assertEqual([(m.level_tag, str(m.message)) for m in get_messages(request)][0],
                         ('success', "Offer '%s' created!" % offer.name))
        self.assertEqual(request.session['offer_wizard'], {})


@freeze_time('2021-04-23 14:00:00')
class TestUpdateOfferWizardStepView(TestCase):

    def setUp(self):
        self.offer = ConditionalOfferFactory()
        self.metadata_form_kwargs_key = 'metadata%s' % self.offer.pk
        self.metadata_obj_key = 'metadata%s_obj' % self.offer.pk
        self.benefit_form_kwargs_key = 'benefit%s' % self.offer.pk
        self.benefit_obj_key = 'benefit%s_obj' % self.offer.pk
        self.condition_form_kwargs_key = 'condition%s' % self.offer.pk
        self.condition_obj_key = 'condition%s_obj' % self.offer.pk
        range_ = RangeFactory()

        self.metadata_form_kwargs_session_data = {
            'data': {
                'name': 'Test offer',
                'slug': self.offer.slug,
                'description': 'Test description',
                'offer_type': ConditionalOffer.VOUCHER,
                'exclusive': True,
                'status': ConditionalOffer.OPEN,
                'condition': self.offer.condition.pk,
                'benefit': self.offer.benefit.pk,
                'priority': 0,
                'start_datetime': None,
                'end_datetime': None,
                'max_global_applications': None,
                'max_user_applications': None,
                'max_basket_applications': None,
                'max_discount': None,
                'total_discount': '0.00',
                'num_applications': 0,
                'num_orders': 0,
                'redirect_url': '',
                'date_created': '2021-04-23T14:00:00Z',
            },
        }
        self.metadata_obj_session_data = [{
            'model': 'offer.conditionaloffer',
            'pk': None,
            'fields': {
                'name': 'Test offer',
                'description': 'Test description',
                'offer_type': ConditionalOffer.VOUCHER,
            },
        }]
        self.benefit_form_kwargs_session_data = {
            'data': {
                'range': range_.pk,
                'type': Benefit.FIXED,
                'value': '2000',
                'max_affected_items': 2,
                'custom_benefit': '',
            },
        }
        self.benefit_obj_session_data = [{
            'model': 'offer.benefit',
            'pk': None,
            'fields': {
                'range': range_.pk,
                'type': Benefit.FIXED,
                'value': '2000',
                'max_affected_items': 2,
                'proxy_class': '',
            },
        }]
        self.condition_form_kwargs_session_data = {
            'data': {
                'range': range_.pk,
                'type': Condition.VALUE,
                'value': '2000',
                'custom_condition': '',
            },
        }
        self.condition_obj_session_data = [{
            'model': 'offer.condition',
            'pk': None,
            'fields': {
                'range': range_.pk,
                'type': Condition.VALUE,
                'value': '2000',
                'proxy_class': '',
            },
        }]

    def test_offer_meta_data_view(self):
        request = RequestFactory().post('/', data={
            'name': 'Test offer',
            'description': 'Test description',
            'offer_type': ConditionalOffer.VOUCHER,
        })
        response = offer_views.OfferMetaDataView.as_view(update=True)(request, pk=self.offer.pk)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:offer-benefit', kwargs={'pk': self.offer.pk}))
        self.assertJSONEqual(request.session['offer_wizard'][self.metadata_form_kwargs_key], {
            'data': {
                'name': 'Test offer',
                'description': 'Test description',
                'offer_type': ConditionalOffer.VOUCHER,
            },
        })
        self.assertJSONEqual(request.session['offer_wizard'][self.metadata_obj_key], [{
            'model': 'offer.conditionaloffer',
            'pk': self.offer.pk,
            'fields': {
                'name': 'Test offer',
                'slug': self.offer.slug,
                'description': 'Test description',
                'offer_type': ConditionalOffer.VOUCHER,
                'exclusive': True,
                'status': ConditionalOffer.OPEN,
                'condition': self.offer.condition.pk,
                'benefit': self.offer.benefit.pk,
                'priority': 0,
                'start_datetime': None,
                'end_datetime': None,
                'max_global_applications': None,
                'max_user_applications': None,
                'max_basket_applications': None,
                'max_discount': None,
                'total_discount': '0.00',
                'num_applications': 0,
                'num_orders': 0,
                'redirect_url': '',
                'date_created': '2021-04-23T14:00:00Z',
            },
        }])

    def test_offer_benefit_view_with_built_in_benefit_type(self):
        range_ = RangeFactory()

        request = RequestFactory().post('/', data={
            'range': range_.pk,
            'type': Benefit.FIXED,
            'value': 2000,
        })
        request.session['offer_wizard'] = {
            self.metadata_form_kwargs_key: json.dumps(self.metadata_form_kwargs_session_data),
            self.metadata_obj_key: json.dumps(self.metadata_obj_session_data),
        }
        response = offer_views.OfferBenefitView.as_view(update=True)(request, pk=self.offer.pk)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:offer-condition', kwargs={'pk': self.offer.pk}))
        self.assertJSONEqual(request.session['offer_wizard'][self.metadata_form_kwargs_key],
                             self.metadata_form_kwargs_session_data)
        self.assertJSONEqual(request.session['offer_wizard'][self.metadata_obj_key], self.metadata_obj_session_data)
        self.assertJSONEqual(request.session['offer_wizard'][self.benefit_form_kwargs_key], {
            'data': {
                'range': range_.pk,
                'type': Benefit.FIXED,
                'value': '2000',
                'max_affected_items': None,
                'custom_benefit': '',
            },
        })
        self.assertJSONEqual(request.session['offer_wizard'][self.benefit_obj_key], [{
            'model': 'offer.benefit',
            'pk': self.offer.benefit.pk,
            'fields': {
                'range': range_.pk,
                'type': Benefit.FIXED,
                'value': '2000',
                'max_affected_items': None,
                'proxy_class': '',
            },
        }])

    def test_offer_benefit_view_with_custom_benefit_type(self):
        benefit = create_benefit(CustomBenefitModel)

        request = RequestFactory().post('/', data={
            'custom_benefit': benefit.pk,
        })
        request.session['offer_wizard'] = {
            self.metadata_form_kwargs_key: json.dumps(self.metadata_form_kwargs_session_data),
            self.metadata_obj_key: json.dumps(self.metadata_obj_session_data),
        }
        response = offer_views.OfferBenefitView.as_view(update=True)(request, pk=self.offer.pk)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:offer-condition', kwargs={'pk': self.offer.pk}))
        self.assertJSONEqual(request.session['offer_wizard'][self.metadata_form_kwargs_key],
                             self.metadata_form_kwargs_session_data)
        self.assertJSONEqual(request.session['offer_wizard'][self.metadata_obj_key], self.metadata_obj_session_data)
        self.assertJSONEqual(request.session['offer_wizard'][self.benefit_form_kwargs_key], {
            'data': {
                'range': None,
                'type': '',
                'value': None,
                'max_affected_items': None,
                'custom_benefit': str(benefit.pk),
            },
        })
        self.assertJSONEqual(request.session['offer_wizard'][self.benefit_obj_key], [{
            'model': 'offer.benefit',
            'pk': benefit.pk,
            'fields': {
                'range': None,
                'type': '',
                'value': None,
                'max_affected_items': None,
                'proxy_class': benefit.proxy_class,
            }
        }])

    def test_offer_condition_view_with_built_in_condition_type(self):
        range_ = RangeFactory()

        request = RequestFactory().post('/', data={
            'range': range_.pk,
            'type': Condition.VALUE,
            'value': 2000,
        })
        request.session['offer_wizard'] = {
            self.metadata_form_kwargs_key: json.dumps(self.metadata_form_kwargs_session_data),
            self.metadata_obj_key: json.dumps(self.metadata_obj_session_data),
            self.benefit_form_kwargs_key: json.dumps(self.benefit_form_kwargs_session_data),
            self.benefit_obj_key: json.dumps(self.benefit_obj_session_data),
        }
        response = offer_views.OfferConditionView.as_view(update=True)(request, pk=self.offer.pk)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:offer-restrictions', kwargs={'pk': self.offer.pk}))
        self.assertJSONEqual(request.session['offer_wizard'][self.metadata_form_kwargs_key],
                             self.metadata_form_kwargs_session_data)
        self.assertJSONEqual(request.session['offer_wizard'][self.metadata_obj_key], self.metadata_obj_session_data)
        self.assertJSONEqual(request.session['offer_wizard'][self.benefit_form_kwargs_key],
                             self.benefit_form_kwargs_session_data)
        self.assertJSONEqual(request.session['offer_wizard'][self.benefit_obj_key], self.benefit_obj_session_data)
        self.assertJSONEqual(request.session['offer_wizard'][self.condition_form_kwargs_key], {
            'data': {
                'range': range_.pk,
                'type': Condition.VALUE,
                'value': '2000',
                'custom_condition': '',
            },
        })
        self.assertJSONEqual(request.session['offer_wizard'][self.condition_obj_key], [{
            'model': 'offer.condition',
            'pk': self.offer.condition.pk,
            'fields': {
                'range': range_.pk,
                'type': Condition.VALUE,
                'value': '2000',
                'proxy_class': '',
            },
        }])

    def test_offer_condition_view_with_custom_condition_type(self):
        condition = create_condition(Condition)

        request = RequestFactory().post('/', data={
            'custom_condition': condition.pk,
        })
        request.session['offer_wizard'] = {
            self.metadata_form_kwargs_key: json.dumps(self.metadata_form_kwargs_session_data),
            self.metadata_obj_key: json.dumps(self.metadata_obj_session_data),
            self.benefit_form_kwargs_key: json.dumps(self.benefit_form_kwargs_session_data),
            self.benefit_obj_key: json.dumps(self.benefit_obj_session_data),
        }
        response = offer_views.OfferConditionView.as_view(update=True)(request, pk=self.offer.pk)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:offer-restrictions', kwargs={'pk': self.offer.pk}))
        self.assertJSONEqual(request.session['offer_wizard'][self.metadata_form_kwargs_key],
                             self.metadata_form_kwargs_session_data)
        self.assertJSONEqual(request.session['offer_wizard'][self.metadata_obj_key], self.metadata_obj_session_data)
        self.assertJSONEqual(request.session['offer_wizard'][self.benefit_form_kwargs_key],
                             self.benefit_form_kwargs_session_data)
        self.assertJSONEqual(request.session['offer_wizard'][self.benefit_obj_key], self.benefit_obj_session_data)
        self.assertJSONEqual(request.session['offer_wizard'][self.condition_form_kwargs_key], {
            'data': {
                'range': None,
                'type': '',
                'value': None,
                'custom_condition': str(condition.pk),
            },
        })
        self.assertJSONEqual(request.session['offer_wizard'][self.condition_obj_key], [{
            'model': 'offer.condition',
            'pk': condition.pk,
            'fields': {
                'range': None,
                'type': '',
                'value': None,
                'proxy_class': condition.proxy_class,
            }
        }])

    def test_offer_restrictions_view(self):
        request = RequestFactory().post('/', data={
            'priority': 0,
        })
        request.session['offer_wizard'] = {
            self.metadata_form_kwargs_key: json.dumps(self.metadata_form_kwargs_session_data),
            self.metadata_obj_key: json.dumps(self.metadata_obj_session_data),
            self.benefit_form_kwargs_key: json.dumps(self.benefit_form_kwargs_session_data),
            self.benefit_obj_key: json.dumps(self.benefit_obj_session_data),
            self.condition_form_kwargs_key: json.dumps(self.condition_form_kwargs_session_data),
            self.condition_obj_key: json.dumps(self.condition_obj_session_data),
        }
        response = offer_views.OfferRestrictionsView.as_view(update=True)(request, pk=self.offer.pk)

        self.offer.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:offer-detail', kwargs={'pk': self.offer.pk}))
        self.assertEqual([(m.level_tag, str(m.message)) for m in get_messages(request)][0],
                         ('success', "Offer '%s' updated" % self.offer.name))
        self.assertEqual(request.session['offer_wizard'], {})


class TestAnAdmin(WebTestCase):
    # New version of offer tests buy using WebTest
    is_staff = True

    def setUp(self):
        super().setUp()
        self.range = models.Range.objects.create(
            name="All products", includes_all_products=True)

    def test_can_create_an_offer(self):
        list_page = self.get(reverse('dashboard:offer-list'))

        metadata_page = list_page.click('Create new offer')
        metadata_form = metadata_page.form
        metadata_form['name'] = "Test offer"
        metadata_form['offer_type'] = models.ConditionalOffer.SITE

        benefit_page = metadata_form.submit().follow()
        benefit_form = benefit_page.form
        benefit_form['range'] = self.range.id
        benefit_form['type'] = "Percentage"
        benefit_form['value'] = "25"

        condition_page = benefit_form.submit().follow()
        condition_form = condition_page.form
        condition_form['range'] = self.range.id
        condition_form['type'] = "Count"
        condition_form['value'] = "3"

        restrictions_page = condition_form.submit().follow()
        restrictions_page.form.submit()

        offers = models.ConditionalOffer.objects.all()
        self.assertEqual(1, len(offers))
        offer = offers[0]
        self.assertEqual("Test offer", offer.name)
        self.assertEqual(3, offer.condition.value)
        self.assertEqual(25, offer.benefit.value)

    def test_offer_list_page(self):
        offer = factories.create_offer(name="Offer A")

        list_page = self.get(reverse('dashboard:offer-list'))
        form = list_page.forms[0]
        form['name'] = "I do not exist"
        res = form.submit()
        self.assertTrue("No offers found" in res.text)

        form['name'] = "Offer A"
        res = form.submit()
        self.assertFalse("No offers found" in res.text)

        form['is_active'] = "true"
        res = form.submit()
        self.assertFalse("No offers found" in res.text)

        yesterday = timezone.now() - timezone.timedelta(days=1)
        offer.end_datetime = yesterday
        offer.save()

        form['is_active'] = "true"
        res = form.submit()
        self.assertTrue("No offers found" in res.text)

        tomorrow = timezone.now() + timezone.timedelta(days=1)
        offer.end_datetime = tomorrow
        offer.save()

        form['offer_type'] = "Site"
        res = form.submit()
        self.assertFalse("No offers found" in res.text)

        form['offer_type'] = "Voucher"
        res = form.submit()
        self.assertTrue("No offers found" in res.text)

    def test_can_update_an_existing_offer(self):
        factories.create_offer(name="Offer A")

        list_page = self.get(reverse('dashboard:offer-list'))
        detail_page = list_page.click('Offer A')

        metadata_page = detail_page.click(linkid="edit_metadata")
        metadata_form = metadata_page.form
        metadata_form['name'] = "Offer A+"
        metadata_form['offer_type'] = models.ConditionalOffer.SITE

        benefit_page = metadata_form.submit().follow()
        benefit_form = benefit_page.form

        condition_page = benefit_form.submit().follow()
        condition_form = condition_page.form

        restrictions_page = condition_form.submit().follow()
        restrictions_page.form.submit()

        models.ConditionalOffer.objects.get(name="Offer A+")

    def test_can_update_an_existing_offer_save_directly(self):
        # see if we can save the offer directly without completing all
        # steps
        offer = factories.create_offer(name="Offer A")
        name_and_description_page = self.get(
            reverse('dashboard:offer-metadata', kwargs={'pk': offer.pk}))
        res = name_and_description_page.form.submit('save').follow()
        self.assertEqual(200, res.status_code)

    def test_can_jump_to_intermediate_step_for_existing_offer(self):
        offer = factories.create_offer()
        url = reverse('dashboard:offer-condition',
                      kwargs={'pk': offer.id})
        self.assertEqual(200, self.get(url).status_code)

    def test_cannot_jump_to_intermediate_step(self):
        for url_name in ('dashboard:offer-condition',
                         'dashboard:offer-benefit',
                         'dashboard:offer-restrictions'):
            response = self.get(reverse(url_name))
            self.assertEqual(302, response.status_code)

    def test_can_suspend_an_offer(self):
        # Create an offer
        offer = factories.create_offer()
        self.assertFalse(offer.is_suspended)

        detail_page = self.get(reverse('dashboard:offer-detail',
                                       kwargs={'pk': offer.pk}))
        form = detail_page.forms['status_form']
        form.submit('suspend')

        offer.refresh_from_db()
        self.assertTrue(offer.is_suspended)

    def test_can_reinstate_a_suspended_offer(self):
        # Create a suspended offer
        offer = factories.create_offer()
        offer.suspend()
        self.assertTrue(offer.is_suspended)

        detail_page = self.get(reverse('dashboard:offer-detail',
                                       kwargs={'pk': offer.pk}))
        form = detail_page.forms['status_form']
        form.submit('unsuspend')

        offer.refresh_from_db()
        self.assertFalse(offer.is_suspended)

    def test_can_change_offer_priority(self):
        offer = factories.create_offer()
        restrictions_page = self.get(reverse('dashboard:offer-restrictions', kwargs={'pk': offer.pk}))
        restrictions_page.form['priority'] = '12'
        restrictions_page.form.submit()
        offer.refresh_from_db()

        self.assertEqual(offer.priority, 12)

    def test_jump_back_to_incentive_step_for_new_offer(self):
        list_page = self.get(reverse('dashboard:offer-list'))

        metadata_page = list_page.click('Create new offer')
        metadata_form = metadata_page.form
        metadata_form['name'] = "Test offer"
        metadata_form['offer_type'] = models.ConditionalOffer.SITE

        benefit_page = metadata_form.submit().follow()
        benefit_form = benefit_page.form
        benefit_form['range'] = self.range.id
        benefit_form['type'] = "Percentage"
        benefit_form['value'] = "25"

        benefit_form.submit()
        benefit_page = self.get(reverse('dashboard:offer-benefit'))
        # Accessing through context because WebTest form does not include an 'errors' field
        benefit_form = benefit_page.context['form']

        self.assertFalse('range' in benefit_form.errors)
        self.assertEqual(len(benefit_form.errors), 0)

    def test_jump_back_to_condition_step_for_new_offer(self):
        list_page = self.get(reverse('dashboard:offer-list'))

        metadata_page = list_page.click('Create new offer')
        metadata_form = metadata_page.form
        metadata_form['name'] = "Test offer"
        metadata_form['offer_type'] = models.ConditionalOffer.SITE

        benefit_page = metadata_form.submit().follow()
        benefit_form = benefit_page.form
        benefit_form['range'] = self.range.id
        benefit_form['type'] = "Percentage"
        benefit_form['value'] = "25"

        condition_page = benefit_form.submit().follow()
        condition_form = condition_page.form
        condition_form['range'] = self.range.id
        condition_form['type'] = "Count"
        condition_form['value'] = "3"

        condition_form.submit()
        condition_page = self.get(reverse('dashboard:offer-condition'))

        self.assertFalse('range' in condition_page.errors)
        self.assertEqual(len(condition_page.errors), 0)

    def test_jump_to_incentive_step_for_existing_offer(self):
        offer = factories.create_offer()
        url = reverse('dashboard:offer-benefit', kwargs={'pk': offer.id})

        condition_page = self.get(url)

        self.assertFalse('range' in condition_page.errors)
        self.assertEqual(len(condition_page.errors), 0)

    def test_jump_to_condition_step_for_existing_offer(self):
        offer = factories.create_offer()
        url = reverse('dashboard:offer-condition', kwargs={'pk': offer.id})

        condition_page = self.get(url)

        self.assertFalse('range' in condition_page.errors)
        self.assertEqual(len(condition_page.errors), 0)

    def test_remove_offer_from_combinations(self):
        offer_a = factories.create_offer("Offer A")
        offer_b = factories.create_offer("Offer B")
        offer_b.exclusive = False
        offer_b.save()

        restrictions_page = self.get(reverse(
            'dashboard:offer-restrictions', kwargs={'pk': offer_a.pk}))
        restrictions_page.form['exclusive'] = False
        restrictions_page.form['combinations'] = [offer_b.id]
        restrictions_page.form.submit()

        self.assertIn(offer_a, offer_b.combinations.all())

        restrictions_page = self.get(reverse(
            'dashboard:offer-restrictions', kwargs={'pk': offer_a.pk}))
        restrictions_page.form['combinations'] = []
        restrictions_page.form.submit()

        self.assertNotIn(offer_a, offer_b.combinations.all())


class TestOfferListSearch(WebTestCase):
    is_staff = True

    TEST_CASES = [
        ({}, []),
        (
            {'name': 'Bob Smith'},
            ['Name matches "Bob Smith"']
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
            {'offer_type': 'Site'},
            ['Is of type "Site offer - available to all users"']
        ),
        (
            {'has_vouchers': True},
            ['Has vouchers']
        ),
        (
            {'has_vouchers': False},
            ['Has no vouchers']
        ),
        (
            {'voucher_code': 'abcd1234'},
            ['Voucher code matches "abcd1234"']
        ),
        (
            {
                'name': 'Bob Smith',
                'is_active': True,
                'offer_type': 'Site',
                'has_vouchers': True,
                'voucher_code': 'abcd1234',
            },
            [
                'Name matches "Bob Smith"',
                'Is active',
                'Is of type "Site offer - available to all users"',
                'Has vouchers',
                'Voucher code matches "abcd1234"',
            ]
        ),
    ]

    def test_search_filter_descriptions(self):
        url = reverse('dashboard:offer-list')
        for params, expected_filters in self.TEST_CASES:
            response = self.get(url, params=params)
            self.assertEqual(response.status_code, 200)
            applied_filters = [
                el.text.strip() for el in
                response.html.select('.search-filter-list .badge')
            ]
            self.assertEqual(applied_filters, expected_filters)
