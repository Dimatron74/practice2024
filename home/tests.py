from django.test import TestCase
from django.urls import reverse
from django.core import mail
from .models import * # Импортируй формы, модели или функции, которые хочешь протестировать
from .views import *
from django.contrib.messages import get_messages

class IndexViewTest(TestCase):
    def setUp(self):
        """Создаем тестовые данные."""
        self.blog1 = Blog.objects.create(
            title='Блог 1', 
            meta='Мета описание 1', 
            content='Содержание 1', 
            category='Категория 1', 
            slug='blog-1'
        )
        self.blog2 = Blog.objects.create(
            title='Блог 2', 
            meta='Мета описание 2', 
            content='Содержание 2', 
            category='Категория 2', 
            slug='blog-2'
        )
        self.blog3 = Blog.objects.create(
            title='Блог 3', 
            meta='Мета описание 3', 
            content='Содержание 3', 
            category='Категория 3', 
            slug='blog-3'
        )

    def test_index_view(self):
        """Проверяем представление index."""
        response = self.client.get(reverse('home:home'))

        self.assertEqual(response.status_code, 200) 
        self.assertTemplateUsed(response, 'index.html')  

        # Проверяем, что контекст содержит правильное количество блогов 
        self.assertEqual(len(response.context['random_blogs']), 3) 

        # Проверяем, что заголовки блогов присутствуют в ответе
        self.assertContains(response, 'Блог 1')
        self.assertContains(response, 'Блог 2')
        self.assertContains(response, 'Блог 3')


class ContactViewTest(TestCase):
    
    def test_contact_form_valid_submission(self):
        """Проверка отправки валидной формы."""
        data = {
            'name': 'Иван Иванов',
            'email': 'test@example.com',
            'phone': '+71234567890',
            'project_type': 'Веб-сайт',
            'budget': '100000',
            'deadline': '2024-12-31',
            'message': 'Тестовое сообщение'
        }
        response = self.client.post(reverse('home:contact'), data, follow=True)
        
        # Проверяем, что форма перенаправляет на ту же страницу
        self.assertRedirects(response, reverse('home:contact'))

        # Проверяем сообщения об успешной отправке
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Ваше сообщение отправлено. Спасибо за проявленный интерес к нам! Скоро мы с вами свяжемся.')

        # Проверяем, что данные сохранены в базе данных
        self.assertTrue(Application.objects.filter(email='test@example.com').exists())

        # Проверяем, что email отправлен
        self.assertEqual(len(mail.outbox), 1) 
        self.assertEqual(mail.outbox[0].subject, 'Спасибо за вашу заявку!')

    def test_contact_form_empty_submission(self):
        """Проверка отправки пустой формы."""
        response = self.client.post(reverse('home:contact'), {}, follow=True)

        # Проверяем сообщения об ошибке
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'One or more fields are empty!')

        # Проверяем, что данные не сохранены в базе данных
        self.assertFalse(Application.objects.exists())

        # Проверяем, что email не отправлен
        self.assertEqual(len(mail.outbox), 0) 

    def test_contact_form_invalid_phone(self):
        """Проверка отправки формы с некорректным телефоном."""
        data = {
            'name': 'Иван Иванов',
            'email': 'test@example.com',
            'phone': 'некорректный телефон',
            'project_type': 'Веб-сайт',
            'budget': '100000',
            'deadline': '2024-12-31',
            'message': 'Тестовое сообщение'
        }
        response = self.client.post(reverse('home:contact'), data, follow=True)

        # Проверяем сообщения об ошибке
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Почта или телефон введены некорректно!')

        # Проверяем, что данные не сохранены в базе данных
        self.assertFalse(Application.objects.filter(email='test@example.com').exists())

        # Проверяем, что email не отправлен
        self.assertEqual(len(mail.outbox), 0)


class SearchViewTest(TestCase):

    def setUp(self):
        """Настраиваем тестовые данные."""

        self.category1 = Category.objects.create(name='Веб-разработка')
        self.category2 = Category.objects.create(name='Мобильная разработка')
        self.technology1 = Technology.objects.create(name='Django', classtype='backend')
        self.technology2 = Technology.objects.create(name='React', classtype='frontend')

        self.blog1 = Blog.objects.create(
            title='Статья про Django', 
            meta='Мета описание статьи про Django',
            content='Это статья про Django', 
            category='Веб-разработка', 
            slug='statya-pro-django'
        )
        self.blog2 = Blog.objects.create(
            title='Новость о React', 
            meta='React',
            content='Вышла новая версия React', 
            category='Фронтенд', 
            slug='novost-o-react'
        )
        self.project1 = Project.objects.create(
            title='Проект на Django', 
            description='Описание проекта на Django', 
            short_description='Django проект',
            image='image.jpg',
        )
        self.project1.categories.add(self.category1)
        self.project1.technologies.add(self.technology1)

        self.project2 = Project.objects.create(
            title='Мобильное приложение', 
            description='Описание мобильного приложения', 
            short_description='Мобильное приложение на React Native',
            image='mobile_app.png', 
        )
        self.project2.categories.add(self.category2)
        self.project2.technologies.add(self.technology2)

    def test_search_by_title(self):
        """Проверяем поиск по заголовку."""
        response = self.client.get(reverse('home:search'), {'q': 'Django'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 2)  # Должны найти статью и проект

    def test_search_by_content(self):
        """Проверяем поиск по содержанию."""
        response = self.client.get(reverse('home:search'), {'q': 'Вышла'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 1)  # Должны найти только новость

    def test_search_by_category(self):
        """Проверяем поиск по категории."""
        response = self.client.get(reverse('home:search'), {'q': 'Веб-разработка'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 1)  # Должны найти только проект

    def test_search_by_technology(self):
        """Проверяем поиск по технологии."""
        response = self.client.get(reverse('home:search'), {'q': 'React'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 2)  # Должны найти новость и проект

    def test_search_no_results(self):
        """Проверяем случай, когда ничего не найдено."""
        response = self.client.get(reverse('home:search'), {'q': 'Какой-то несуществующий запрос'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 0)
        self.assertEqual(response.context['message'], "Извините, по вашему запросу ничего не найдено.")

    def test_search_multiple_terms(self):
        """Проверяем поиск по нескольким словам."""
        response = self.client.get(reverse('home:search'), {'q': 'Django React'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 3)  # Должны найти и статью, и новость, и проект

    def test_search_with_empty_query(self):
        """Проверяем поиск с пустым запросом."""
        response = self.client.get(reverse('home:search'), {'q': ''})
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.context['results']), 1)


class ProjectsViewTest(TestCase):

    def setUp(self):
        """Создаем тестовые данные."""
        self.project1 = Project.objects.create(
            title='Проект 1',
            description='Описание проекта 1',
            short_description='Проект 1',
            image='image1.jpg'
        )
        self.project2 = Project.objects.create(
            title='Проект 2',
            description='Описание проекта 2',
            short_description='Проект 2',
            image='image2.jpg'
        )
        self.project3 = Project.objects.create(
            title='Проект 3',
            description='Описание проекта 3',
            short_description='Проект 3',
            image='image3.jpg'
        )
        self.project4 = Project.objects.create(
            title='Проект 4',
            description='Описание проекта 4',
            short_description='Проект 4',
            image='image4.jpg'
        )

    def test_projects_view_first_page(self):
        """Проверяем первую страницу пагинации."""
        response = self.client.get(reverse('home:projects'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects.html')
        self.assertEqual(len(response.context['projects']), 3)  # 3 проекта на первой странице
        self.assertTrue(response.context['projects'].has_next()) # Должна быть следующая страница
        self.assertFalse(response.context['projects'].has_previous()) # Не должно быть предыдущей страницы

    def test_projects_view_second_page(self):
        """Проверяем вторую страницу пагинации."""
        response = self.client.get(reverse('home:projects') + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['projects']), 1)  # 1 проект на второй странице
        self.assertFalse(response.context['projects'].has_next()) # Не должно быть следующей страницы
        self.assertTrue(response.context['projects'].has_previous()) # Должна быть предыдущая страница

    def test_projects_view_invalid_page(self):
        """Проверяем обработку неверного номера страницы."""
        response = self.client.get(reverse('home:projects') + '?page=abc')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['projects']), 3)  # Должна вернуться первая страница

    def test_projects_view_out_of_range_page(self):
        """Проверяем обработку номера страницы вне диапазона."""
        response = self.client.get(reverse('home:projects') + '?page=100')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['projects']), 1) 