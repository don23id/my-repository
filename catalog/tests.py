import datetime
from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.contrib.messages import get_messages

from .models import (
    Category, CollectibleItem, Comment, Vote, UserCollection,
    Poll, PollOption, PollVote, VisitCount
)
from .forms import CommentForm, PollVoteForm, VoteForm  # VoteForm wasn't used in views but exists


# Helper functions to create objects
def create_user(username='testuser', password='password123'):
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        return User.objects.create_user(username=username, password=password)


def create_category(name='Test Category', slug=None):
    if slug is None:
        from django.utils.text import slugify
        slug = slugify(name)
    return Category.objects.create(name=name, slug=slug)


def create_item(category, name='Test Item', slug=None):
    if slug is None:
        from django.utils.text import slugify
        slug = slugify(name)
    return CollectibleItem.objects.create(
        name=name,
        slug=slug,
        category=category,
        description='Test description',
        country='Testland',
        condition='UNC'
    )


def create_poll(question='Test Poll Question?', is_active=True):
    return Poll.objects.create(question=question, is_active=is_active)


def create_poll_option(poll, text='Test Option'):
    return PollOption.objects.create(poll=poll, text=text)


class ModelTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.category = create_category(name="Coins")
        self.item = create_item(self.category, name="Rare Coin")
        self.poll = create_poll(question="Favorite Color?")
        self.option = create_poll_option(self.poll, text="Blue")

    def test_category_str(self):
        self.assertEqual(str(self.category), "Coins")

    def test_category_save_slug(self):
        category_no_slug = Category.objects.create(name="New Category No Slug")
        self.assertEqual(category_no_slug.slug, "new-category-no-slug")

    def test_category_get_absolute_url(self):
        self.assertEqual(self.category.get_absolute_url(),
                         reverse('category_detail', kwargs={'slug': self.category.slug}))

    def test_collectible_item_str(self):
        self.assertEqual(str(self.item), "Rare Coin")

    def test_collectible_item_save_slug(self):
        item_no_slug = CollectibleItem.objects.create(name="Shiny New Item", category=self.category, description="d",
                                                      country="c", condition="F")
        self.assertEqual(item_no_slug.slug, "shiny-new-item")

    def test_collectible_item_get_absolute_url(self):
        self.assertEqual(self.item.get_absolute_url(), reverse('item_detail', kwargs={'slug': self.item.slug}))

    def test_comment_str(self):
        comment = Comment.objects.create(item=self.item, user=self.user, text="Nice!")
        self.assertEqual(str(comment), f'{self.user.username} - {self.item.name}')

    def test_vote_str(self):
        vote_like = Vote.objects.create(item=self.item, user=self.user, value=True)
        self.assertEqual(str(vote_like), f'{self.user.username} - Лайк - {self.item.name}')
        # Need a new user or item for a new vote record due to unique_together
        user2 = create_user(username="user2")
        vote_dislike = Vote.objects.create(item=self.item, user=user2, value=False)
        self.assertEqual(str(vote_dislike), f'{user2.username} - Дизлайк - {self.item.name}')

    def test_user_collection_str(self):
        collection_entry = UserCollection.objects.create(user=self.user, item=self.item)
        self.assertEqual(str(collection_entry), f'{self.user.username} - {self.item.name}')

    def test_visit_count_str(self):
        today = datetime.date.today()
        visit = VisitCount.objects.create(date=today, count=5)
        self.assertEqual(str(visit), f'{today} - 5 посещений')

    def test_poll_str(self):
        self.assertEqual(str(self.poll), "Favorite Color?")

    def test_poll_option_str(self):
        self.assertEqual(str(self.option), "Blue")

    def test_poll_vote_str(self):
        poll_vote = PollVote.objects.create(poll=self.poll, option=self.option, user=self.user)
        self.assertEqual(str(poll_vote), f'{self.user.username} - {self.option.text}')


class FormTests(TestCase):
    def setUp(self):
        self.poll = create_poll()
        self.option1 = create_poll_option(self.poll, "Option A")
        self.option2 = create_poll_option(self.poll, "Option B")

    def test_comment_form_valid(self):
        form = CommentForm(data={'text': 'A valid comment.'})
        self.assertTrue(form.is_valid())

    def test_comment_form_invalid_empty(self):
        form = CommentForm(data={'text': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)

    def test_vote_form_valid(self):  # Though not used directly in views, it's good to test
        form = VoteForm(data={'value': True})
        self.assertTrue(form.is_valid())
        form = VoteForm(data={'value': False})
        self.assertTrue(form.is_valid())

    def test_poll_vote_form_initialization_and_valid(self):
        form = PollVoteForm(poll=self.poll, data={'option': self.option1.id})
        self.assertTrue(form.is_valid())
        self.assertIn((self.option1.id, self.option1.text), form.fields['option'].choices)
        self.assertIn((self.option2.id, self.option2.text), form.fields['option'].choices)

    def test_poll_vote_form_invalid_choice(self):
        form = PollVoteForm(poll=self.poll, data={'option': 999})  # Non-existent option
        self.assertFalse(form.is_valid())
        self.assertIn('option', form.errors)


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_user(username="viewtestuser")
        self.category = create_category(name="View Category", slug="view-category")
        self.item = create_item(self.category, name="View Item", slug="view-item")
        self.poll = create_poll(question="View Test Poll")
        self.option1 = create_poll_option(self.poll, text="View Option 1")
        self.option2 = create_poll_option(self.poll, text="View Option 2")

    def test_index_view_anonymous(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/index.html')
        self.assertIn('items', response.context)
        self.assertIn('categories', response.context)
        self.assertEqual(response.context['poll'], self.poll)
        self.assertNotIn('user_voted', response.context)
        self.assertNotIn('poll_form', response.context)

    def test_index_view_authenticated_poll_not_voted(self):
        self.client.login(username=self.user.username, password='password123')
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['poll'], self.poll)
        self.assertFalse(response.context['user_voted'])
        self.assertIsInstance(response.context['poll_form'], PollVoteForm)

    def test_index_view_authenticated_poll_voted(self):
        self.client.login(username=self.user.username, password='password123')
        PollVote.objects.create(poll=self.poll, option=self.option1, user=self.user)
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user_voted'])
        self.assertIn('poll_options', response.context)
        self.assertEqual(response.context['total_votes'], 1)

    def test_category_list_view(self):
        response = self.client.get(reverse('category_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/category_list.html')
        self.assertIn(self.category, response.context['categories'])

    def test_category_detail_view(self):
        response = self.client.get(reverse('category_detail', kwargs={'slug': self.category.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/category_detail.html')
        self.assertEqual(response.context['category'], self.category)
        self.assertIn(self.item, response.context['items'])

    def test_item_detail_view_authenticated(self):
        self.client.login(username=self.user.username, password='password123')
        UserCollection.objects.create(user=self.user, item=self.item)
        Vote.objects.create(user=self.user, item=self.item, value=True)  # Like

        response = self.client.get(reverse('item_detail', kwargs={'slug': self.item.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/item_detail.html')
        self.assertEqual(response.context['item'], self.item)
        self.assertTrue(response.context['in_collection'])
        self.assertEqual(response.context['user_vote'], True)
        self.assertEqual(response.context['likes'], 1)
        self.assertIn('hitcount', response.context)  # From HitCountDetailView

    def test_add_comment_view(self):
        self.client.login(username=self.user.username, password='password123')
        url = reverse('add_comment', kwargs={'slug': self.item.slug})
        response = self.client.post(url, {'text': 'A test comment'})
        self.assertRedirects(response, reverse('item_detail', kwargs={'slug': self.item.slug}))
        self.assertTrue(Comment.objects.filter(item=self.item, user=self.user, text='A test comment').exists())
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Комментарий успешно добавлен!')

    def test_vote_item_view(self):
        self.client.login(username=self.user.username, password='password123')
        url = reverse('vote_item', kwargs={'slug': self.item.slug})
        response = self.client.post(url, {'value': 'true'})  # Like
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['likes'], 1)
        self.assertTrue(Vote.objects.filter(item=self.item, user=self.user, value=True).exists())

    def test_user_collection_view(self):
        self.client.login(username=self.user.username, password='password123')
        UserCollection.objects.create(user=self.user, item=self.item)
        response = self.client.get(reverse('user_collection'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/user_collection.html')
        self.assertIn(self.item, [uc.item for uc in response.context['collection_items']])

    def test_vote_poll_view_success(self):
        self.client.login(username=self.user.username, password='password123')
        url = reverse('vote_poll', kwargs={'poll_id': self.poll.id})
        response = self.client.post(url, {'option': self.option1.id})
        self.assertRedirects(response, reverse('index'))
        self.assertTrue(PollVote.objects.filter(poll=self.poll, option=self.option1, user=self.user).exists())
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Ваш голос учтен!')

    def test_vote_poll_view_already_voted(self):
        self.client.login(username=self.user.username, password='password123')
        PollVote.objects.create(poll=self.poll, option=self.option1, user=self.user)  # User already voted
        url = reverse('vote_poll', kwargs={'poll_id': self.poll.id})
        response = self.client.post(url, {'option': self.option2.id})
        self.assertRedirects(response, reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Вы уже голосовали в этом опросе')


class MiddlewareTests(TestCase):
    def setUp(self):
        self.client = Client()
        VisitCount.objects.all().delete()  # Clean slate

    @patch('catalog.middleware.datetime')  # Patch where datetime is imported in your middleware
    def test_visit_counter_new_visit_get_request(self, mock_datetime):
        test_date = datetime.date(2023, 10, 26)
        mock_datetime.date.today.return_value = test_date

        response = self.client.get(reverse('index'))  # Non-AJAX GET
        self.assertEqual(response.status_code, 200)
        self.assertTrue(VisitCount.objects.filter(date=test_date, count=1).exists())
        self.assertTrue(self.client.session.get(f'visited_day_{test_date.isoformat()}'))

        # Second request same session, same day - count should not increase
        self.client.get(reverse('category_list'))
        visit_count = VisitCount.objects.get(date=test_date)
        self.assertEqual(visit_count.count, 1)

    @patch('catalog.middleware.datetime')
    def test_visit_counter_ajax_request_not_counted(self, mock_datetime):
        test_date = datetime.date(2023, 10, 27)
        mock_datetime.date.today.return_value = test_date

        self.client.get(reverse('index'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertFalse(VisitCount.objects.filter(date=test_date).exists())

    @patch('catalog.middleware.datetime')
    def test_visit_counter_post_request_not_counted(self, mock_datetime):
        test_date = datetime.date(2023, 10, 28)
        mock_datetime.date.today.return_value = test_date

        # For a POST, we need a user and an item for add_comment if we use that URL
        user = create_user(username="middleware_user")
        category = create_category("middleware_cat")
        item = create_item(category, "middleware_item")
        self.client.login(username=user.username, password='password123')

        self.client.post(reverse('add_comment', kwargs={'slug': item.slug}), {'text': 'test'})
        self.assertFalse(VisitCount.objects.filter(date=test_date).exists())

    @patch('catalog.middleware.datetime')
    def test_visit_counter_excluded_paths_not_counted(self, mock_datetime):
        test_date = datetime.date(2023, 10, 29)
        mock_datetime.date.today.return_value = test_date

        self.client.get('/admin/')
        self.client.get('/static/some.css')
        self.client.get('/media/some.png')
        self.assertFalse(VisitCount.objects.filter(date=test_date).exists())