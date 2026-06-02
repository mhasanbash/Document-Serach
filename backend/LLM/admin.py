from django.contrib import admin
from .models import Documents, QueryAndAnswer


@admin.register(Documents)
class DocumentsAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'uploaded_file', 'is_processed', 'created_at', 'updated_at')
    
    search_fields = ('title', 'raw_text',)
    
    list_filter = ('is_processed', 'created_at', 'updated_at')

@admin.register(QueryAndAnswer)
class QueryAndAnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'query', 'awnser', 'date_created')
    
    search_fields = ('query', 'awnser')
    
    list_filter = ('date_created',)