from django.core import mail
from django.urls import reverse
from oscar.core.loading import get_model

from ecommerce.test.factories import UserFactory
from ecommerce.test.testcases import WebTestCase

CommunicationEventType = get_model('communication', 'CommunicationEventType')


class TestAnAdmin(WebTestCase):

    def setUp(self):
        self.staff = UserFactory(is_staff=True, username='1234')
        self.commtype = CommunicationEventType.objects.create(
            name="Password reset",
            category=CommunicationEventType.USER_RELATED)

    def test_can_preview_an_email(self):
        list_page = self.app.get(
            reverse('dashboard:comms-list'), user=self.staff)
        update_page = list_page.click('Edit')
        form = update_page.form
        form['email_subject_template'] = 'Hello {{ user.username }}'
        form['email_body_template'] = 'Hello {{ user.username }}'
        form['email_body_html_template'] = 'Hello {{ user.username }}'
        preview = form.submit('show_preview')
        assert 'Hello 1234' in preview.content.decode('utf8')

    def test_can_send_a_preview_email(self):
        list_page = self.app.get(
            reverse('dashboard:comms-list'), user=self.staff)
        update_page = list_page.click('Edit')
        form = update_page.form
        form['email_subject_template'] = 'Hello {{ user.username }}'
        form['email_body_template'] = 'Hello {{ user.username }}'
        form['email_body_html_template'] = 'Hello {{ user.username }}'
        form['preview_email'] = 'testing@example.com'
        form.submit('send_preview')

        assert len(mail.outbox) == 1
