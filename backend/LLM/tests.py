from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Documents
from rest_framework.test import APIClient

# Create your tests here.

class DocumentModelTest(TestCase):
    def test_document_creation(self):
        doc = Documents.objects.create(
            title="test.docx",
            uploaded_file=SimpleUploadedFile("test.docx", b"dummy content"),
            is_processed=False
        )
        self.assertEqual(doc.title, "test.docx")
        self.assertFalse(doc.is_processed)
        
        
class PromptViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.query = "این متن راجب چیست؟"

    def test_prompt_success(self):
        response = self.client.post('/models/prompt/', {'query': self.query}, format='json')
        self.assertEqual(response.status_code, 200)