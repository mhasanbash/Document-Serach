from django.db import models

# Create your models here.

class Documents(models.Model):
    title = models.CharField(max_length=255, unique=True, default="sample.docx")
    uploaded_file = models.FileField(upload_to="documents/")
    is_processed = models.BooleanField(default=False)
    chroma_uuid = models.CharField(max_length=36, blank=True, null=True)
    raw_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title or ""
    

class QueryAndAnswer(models.Model):
    query = models.TextField(blank=True, null=True)
    awnser = models.TextField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.query[:16]


