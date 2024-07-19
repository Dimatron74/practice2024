from django.shortcuts import render, redirect
from home.models import *
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.db.models import Q
import random
import re

# Create your views here.
def index (request):
    blogs = Blog.objects.all().order_by('-time')[:3]
    #random_blogs = random.sample(list(blogs), 3)
    context = {'random_blogs': blogs}
    return render(request, 'index.html', context)

def about (request):
    return render(request, 'about.html')

def thanks(request):
    return render(request, 'thanks.html')


from django.utils.html import escape
def contact(request):
    if request.method == 'POST':
        name = escape(request.POST.get('name', ''))
        email = escape(request.POST.get('email', ''))
        phone = escape(request.POST.get('phone', ''))
        project_type = escape(request.POST.get('project_type', ''))
        budget = escape(request.POST.get('budget', ''))
        deadline = request.POST.get('deadline')
        message = escape(request.POST.get('message', ''))

        # Проверка на пустые значения
        if not all([name, email, message, project_type, budget]):
            messages.error(request, 'One or more fields are empty!')
        else:
            email_pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
            phone_pattern = re.compile(r'^(?:\+7|8)[0-9]{10}$')

            if not deadline:  # Если поле deadline пустое
               deadline = None
            if email_pattern.match(email) and (phone_pattern.match(phone) or not phone):
                # Используем ORM Django для создания объекта и сохранения в базе данных
                application = Application.objects.create(
                    name=name,
                    email=email,
                    phone=phone,
                    project_type=project_type,
                    budget=budget,
                    deadline=deadline,
                    message=message
                )

                # Отправка email-уведомления
                subject = 'Спасибо за вашу заявку!'
                message = f'Здравствуйте, {name}!\n\nМы получили вашу заявку и скоро свяжемся с вами.\n\nС уважением,\nКоманда Pixel Creative'
                from_email = 'Pixel Creative<logachev_16@bk.ru>'
                recipient_list = [email]

                send_mail(subject, message, from_email, recipient_list, fail_silently=False)

                messages.success(request, 'Ваше сообщение отправлено. Спасибо за проявленный интерес к нам! Скоро мы с вами свяжемся.')
                return redirect('home:contact') 
            else:
                messages.error(request, 'Почта или телефон введены некорректно!')

    return render(request, 'contact.html', {})

#УЯЗВИМЫЙ К SQL ИНЪЕКЦИИ
# def contact(request):
#     if request.method == 'POST':
#         name = request.POST.get('name')
#         email = request.POST.get('email')
#         phone = request.POST.get('phone')
#         project_type = request.POST.get('project_type')
#         budget = request.POST.get('budget')
#         deadline = request.POST.get('deadline')
#         message = request.POST.get('message')
        
#         invalid_input = ['', ' ']  # Проверяем все поля на пустоту

#         if name in invalid_input or email in invalid_input or message in invalid_input or project_type in invalid_input or budget in invalid_input:
#             messages.error(request, 'One or more fields are empty!')
#         else:
#             email_pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
#             phone_pattern = re.compile(r'^(?:\+7|8)[0-9]{10}$')
#             if not deadline:  # Если поле deadline пустое
#                 deadline = None
#             if email_pattern.match(email) and (phone_pattern.match(phone) or phone in invalid_input):
#                 application = Application(
#                     name=name,
#                     email=email,
#                     phone=phone,
#                     project_type=project_type,
#                     budget=budget,
#                     deadline=deadline, 
#                     message=message
#                 )
#                 application.save()

#                 # Отправка email-уведомления
#                 subject = 'Спасибо за вашу заявку!'
#                 message = f'Здравствуйте, {name}!\n\nМы получили вашу заявку и скоро свяжемся с вами.\n\nС уважением,\nКоманда Pixel Creative'
#                 from_email = 'Pixel Creative<logachev_16@bk.ru>'
#                 recipient_list = [email]  # Email клиента

#                 send_mail(subject, message, from_email, recipient_list, fail_silently = False)

#                 messages.success(request, 'Ваше сообщение отправлено. Спасибо за проявленный интерес к нам! Скоро мы с вами свяжемся.')
#                 return redirect('contact')  # Редирект 
#             else:
#                 messages.error(request, 'Почта или телефон введены некорректно!')

#     return render(request, 'contact.html', {})

def projects(request):
    project_list = Project.objects.all().order_by('-updated_at')
    paginator = Paginator(project_list, 3) 
    page = request.GET.get('page', '')

    try:
        projects = paginator.page(page)
    except PageNotAnInteger:
        # Если страница не целое число, возвращаем первую страницу
        projects = paginator.page(1)
    except EmptyPage:
        # Если страница выходит за пределы допустимого диапазона,
        # возвращаем последнюю страницу результатов
        projects = paginator.page(paginator.num_pages)

    context = {'projects': projects}
    return render(request, 'projects.html', context)

def blog(request):
    blogs_list = Blog.objects.all().order_by('-time')

    paginator = Paginator(blogs_list, 3)  # По 3 блога на страницу
    page = request.GET.get('page', '')
    try:
        blogs = paginator.page(page)
    except PageNotAnInteger:
        # Если страница не целое число, возвращаем первую страницу
        blogs = paginator.page(1)
    except EmptyPage:
        # Если страница выходит за пределы допустимого диапазона,
        # возвращаем последнюю страницу результатов
        blogs = paginator.page(paginator.num_pages)

    context = {'blogs': blogs}
    return render(request, 'blog.html', context)

def category(request, category):
    category_posts = Blog.objects.filter(category=category).order_by('-time')
    if not category_posts:
        message = f"No posts found in category: '{category}'"
        return render(request, "category.html", {"message": message})
    paginator = Paginator(category_posts, 3)
    page = request.GET.get('page', '')
    category_posts = paginator.get_page(page)
    return render(request, "category.html", {"category": category, 'category_posts': category_posts})

def categories(request):
    all_categories = Blog.objects.values('category').distinct().order_by('category')
    return render(request, "categories.html", {'all_categories': all_categories})


def search(request):
    query = request.GET.get('q', '')
    query_list = query.split()

    blog_results = Blog.objects.none()
    project_results = Project.objects.none()

    # Используем множества для отслеживания уникальных ID объектов
    blog_ids = set()
    project_ids = set()

    for word in query_list:
        # Поиск по Blog
        blogs = Blog.objects.filter(
            Q(title__icontains=word) | Q(content__icontains=word) | Q(meta__icontains=word)
        )
        blog_results |= blogs
        blog_ids.update(blogs.values_list('pk', flat=True))  # Добавляем ID в множество

        # Поиск по Project
        projects = Project.objects.filter(
            Q(title__icontains=word) | Q(short_description__icontains=word)
        )
        project_results |= projects
        project_ids.update(projects.values_list('pk', flat=True))  # Добавляем ID в множество

        # Поиск по Category (применяется к Project)
        category_results = Category.objects.filter(name__icontains=word)
        for category in category_results:
            projects = Project.objects.filter(categories=category)
            project_results |= projects
            project_ids.update(projects.values_list('pk', flat=True))  # Добавляем ID в множество
        
        technology_results = Technology.objects.filter(name__icontains=word)
        for technology in technology_results:
            projects = Project.objects.filter(technologies=technology)
            project_results |= projects
            project_ids.update(projects.values_list('pk', flat=True))


    if not query_list: # Если запрос пустой
        # Извлекаем уникальные объекты по ID
        blog_results = Blog.objects.all().order_by('-time')
        project_results = Project.objects.all().order_by('-created_at')
        # Объединяем результаты
        results = list(blog_results) + list(project_results)
    else:
        blog_results = Blog.objects.filter(pk__in=blog_ids).order_by('-time')
        project_results = Project.objects.filter(pk__in=project_ids).order_by('-created_at')
        results = list(blog_results) + list(project_results)

    # Пагинация
    paginator = Paginator(results, 3)
    page = request.GET.get('page', '')
    try:
        results = paginator.page(page)
    except PageNotAnInteger:
        results = paginator.page(1)
    except EmptyPage:
        results = paginator.page(paginator.num_pages)

    # Сообщение об отсутствии результатов
    if len(results) == 0:
        message = "Извините, по вашему запросу ничего не найдено."
    else:
        message = ""
    context = {
        'results': [{'object': obj, 'type': obj._meta.model_name} for obj in results], # Передаем тип объекта
        'query': query,
        'message': message,
        'page_obj': results, # для пагинатора
    }

    return render(request, 'search.html', context)


#Дальше - неуспешная реализация

    # return render(request, 'search.html', {'results': results, 'query': query, 'message': message})

# def search(request):
#     query = request.GET.get('q')
#     query_list = query.split()

#     blog_results = Blog.objects.none()
#     project_results = Project.objects.none()

#     # Обрабатываем каждое слово из запроса
#     for word in query_list:
#         # Поиск по Blog
#         blog_results |= Blog.objects.filter(
#             Q(title__icontains=word) | Q(content__icontains=word)
#         ).order_by('-time')

#         # Поиск по Project
#         project_results |= Project.objects.filter(
#             Q(title__icontains=word) | Q(description__icontains=word) | Q(short_description__icontains=word) | Q(short_description__icontains=word)
#         ).order_by('-created_at')

#         # Поиск по Category (применяется к Project)
#         category_results = Category.objects.filter(name__icontains=word)
#         for category in category_results:
#             project_results |= Project.objects.filter(categories=category).order_by('-created_at')

#     # Объединяем результаты в список
#     results = list(blog_results) + list(project_results)

#     # Пагинация
#     paginator = Paginator(results, 3)
#     page = request.GET.get('page')
#     try:
#         results = paginator.page(page)
#     except PageNotAnInteger:
#         results = paginator.page(1)
#     except EmptyPage:
#         results = paginator.page(paginator.num_pages)

#     # Сообщение об отсутствии результатов
#     if len(results) == 0:
#         message = "Извините, по вашему запросу ничего не найдено."
#     else:
#         message = ""

#     return render(request, 'search.html', {'results': results, 'query': query, 'message': message})


# def search(request):
#     query = request.GET.get('q')
#     query_list = query.split()
#     results = Blog.objects.none()
#     for word in query_list:
#         results = results | Blog.objects.filter(Q(title__contains=word) | Q(content__contains=word)).order_by('-time')

#     paginator = Paginator(results, 3)
#     page = request.GET.get('page')
#     results = paginator.get_page(page)
#     if len(results) == 0:
#         message = "Sorry, no results found for your search query."
#     else:
#         message = ""
#     return render(request, 'search.html', {'results': results, 'query': query, 'message': message})



def blogpost (request, slug):
    try:
        blog = Blog.objects.get(slug=slug)
        context = {'blog': blog}
        return render(request, 'blogpost.html', context)
    except Blog.DoesNotExist:
        context = {'message': 'Новость не найдена'}
        return render(request, '404.html', context, status=404)