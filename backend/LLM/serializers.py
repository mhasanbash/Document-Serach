from rest_framework import serializers
from .models import Documents, QueryAndAnswer

class QuerySerializer(serializers.Serializer):
    query = serializers.CharField(required=True, help_text="سوالی که کاربر می‌پرسد")
    
    
class DocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documents
        fields = ['uploaded_file', 'title']
        
class DocumentsUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documents
        fields = ['uploaded_file']
        
class QueryAndAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryAndAnswer
        fields = "__all__"