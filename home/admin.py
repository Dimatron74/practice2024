from django.contrib import admin
from django import forms
from django.shortcuts import redirect
from django.http import HttpResponse
from django.utils.encoding import escape_uri_path
from django.template.loader import render_to_string, get_template
from django.contrib.staticfiles import finders
from django.conf import settings
from xhtml2pdf import pisa
import csv
import io
from datetime import datetime 
import os

from home.models import *

# Register your models here.
class BlogAdminForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea(attrs={'id': "richtext_field"}))

    class Meta:
        model = Blog
        fields = "__all__"

class BlogAdmin(admin.ModelAdmin):
    form = BlogAdminForm

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'short_description', 'created_at')  # Поля для отображения в списке
    list_filter = ('categories', 'technologies')  # Фильтры по категориям и технологиям
    search_fields = ('title', 'description')

class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'project_type', 'budget', 'deadline', 'created_at')
    search_fields = ('name', 'email', 'phone', 'project_type', 'budget', 'message')
    list_filter = ('project_type', 'created_at')
    @admin.action(description="Экспортировать в CSV")
    def export_as_csv(self, request, queryset):
        """
        Экспортирует выбранные записи в CSV-файл с поддержкой кириллицы.
        """
        if not queryset.exists():
            return redirect(request.path)  # Перенаправление, если ничего не выбрано
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{timestamp}_{self.model._meta.verbose_name}.csv"
        encoded_filename = escape_uri_path(filename)
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{encoded_filename}"'

        # Создаем объект StringIO с кодировкой UTF-8
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer, quoting=csv.QUOTE_ALL) 
        writer.writerow(['name', 'email', 'phone', 'project_type', 'budget', 'deadline', 'message', 'created_at'])

        for obj in queryset:
            writer.writerow([
                obj.name, 
                obj.email, 
                obj.phone, 
                obj.project_type, 
                obj.budget, 
                obj.deadline, 
                obj.message, 
                obj.created_at.strftime('%Y-%m-%d %H:%M:%S'),  # Форматируем дату и время
            ])

        # Перемещаем содержимое StringIO в ответ
        response.write(csv_buffer.getvalue()) 
        
        return response
    

    @admin.action(description="Экспортировать в PDF")
    def export_as_pdf(self, request, queryset):
        if not queryset.exists():
            return redirect(request.path)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{timestamp}_applications.pdf"
        encoded_filename = escape_uri_path(filename)

        template = get_template('admin/pdf.html')
        context = {'applications': queryset}
        html = template.render(context)
        
        result = io.BytesIO()

        # Функция для поиска ресурсов PDF
        def link_callback(uri, rel):
            """
            Конвертирует HTML URI в абсолютные пути системы, чтобы xhtml2pdf мог получить доступ к этим
            ресурсам.
            """
            result = finders.find(uri)
            if result:
                if not isinstance(result, (list, tuple)):
                    result = [result]
                result = list(os.path.realpath(path) for path in result)
                path = result[0]
            else:
                sUrl = settings.STATIC_URL  # Обычно /static/
                sRoot = settings.STATIC_ROOT  # Обычно /home/userX/project_static/
                mUrl = settings.MEDIA_URL  # Обычно /media/
                mRoot = settings.MEDIA_ROOT  # Обычно /home/userX/project_static/media/

                if uri.startswith(mUrl):
                    path = os.path.join(mRoot, uri.replace(mUrl, ""))
                elif uri.startswith(sUrl):
                    path = os.path.join(sRoot, uri.replace(sUrl, ""))
                else:
                    return uri

            # Убедитесь, что файл существует
            if not os.path.isfile(path):
                raise RuntimeError(
                    'URI медиа-файла должен начинаться с %s или %s' % (sUrl, mUrl)
                )
            return path

        # Создайте PDF
        pdf = pisa.CreatePDF(
            io.BytesIO(html.encode('UTF-8')),
            result,
            encoding='utf-8',
            link_callback=link_callback
        )

        if pdf.err:
            return HttpResponse('Ошибка при создании PDF-файла', status=500)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{encoded_filename}"'
        response.write(result.getvalue())
        return response

    actions = [export_as_csv]
    #actions = [export_as_csv, export_as_pdf]

    


admin.site.register(Application, ApplicationAdmin)
admin.site.register(Blog, BlogAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Technology)
admin.site.register(Category)