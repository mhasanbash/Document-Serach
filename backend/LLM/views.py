from django.shortcuts import render
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.parsers import MultiPartParser, FormParser

from .serializers import (
    QuerySerializer,
    DocumentsSerializer, 
    DocumentsUpdateSerializer, 
    QueryAndAnswerSerializer
)

from .models import (
    Documents, 
    QueryAndAnswer
)

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_kreuzberg import KreuzbergLoader

from .chroma_service import ChromaService

import os
import tempfile
import environ

env = environ.Env()
environ.Env.read_env(settings.BASE_DIR / ".env")

        
class DocumentAddView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        if 'uploaded_file' in data:
            data['title'] = data['uploaded_file'].name 
        
        serializer = DocumentsSerializer(data=data)
        
        if serializer.is_valid():
            document = serializer.save()
            ChromaService().index_document(document)
            
            return Response({"message": "فایل با موفقیت آپلود و پردازش شد"}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
           
class DocumentDeleteView(APIView):
    def delete(self, request, *args, **kwargs):
        title = kwargs.get('title')
        if not title:
            return Response({"error": "title is required"}, status=400)
        doc = get_object_or_404(Documents, title=title)
        ChromaService().delete_document(doc)
        os.remove(doc.uploaded_file.path)
        doc.delete()
        return Response(status=204)
    
class DocumentUpdateView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    
    def _save_temporary_file(self, uploaded_file):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
            for chunk in uploaded_file.chunks():
                tmp_file.write(chunk)
            return tmp_file.name

    def put(self, request, *args, **kwargs):
        data = request.data.copy()
        
        new_file = data['uploaded_file']
        title = data['uploaded_file'].name
        
        doc = get_object_or_404(Documents, title=title)
        
        new_text = ""
        
        try:
            new_file_path = self._save_temporary_file(new_file)
            loader = KreuzbergLoader(file_path=new_file_path)
            new_text = loader.load()[0].page_content
            os.remove(new_file_path)
        except Exception as e:
            return Response({"error": f"Failed to read new file: {str(e)}"}, status=400)
        
        if doc.raw_text == new_text:
            return Response({"message": "No changes detected"}, status=status.HTTP_200_OK)
        
        
        #remove older file and older vector
        ChromaService().delete_document(doc)
        os.remove(doc.uploaded_file.path)
        
        #update file
        doc.uploaded_file = new_file
        doc.raw_text = new_text
        doc.save()
        ChromaService().index_document(doc)

        return Response({"message": "Document updated successfully", "id": doc.id}, status=status.HTTP_200_OK)
        
class PromptToModel(APIView):
    def post(self, request):
        
        serializer = QuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        query = serializer.validated_data.get('query')
        
        try:
            chroma_service = ChromaService()
            top_results = chroma_service.search_across_documents(query, k_per_doc=2, max_total=6)
            
            context_parts = []
            for idx, res in enumerate(top_results, 1):
                context_parts.append(f"[doc {idx} - {res['doc_title']}]:\n{res['content']}")
            context = "\n\n".join(context_parts)

            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "تو یک دستیار سخنگو هستی. به سوال بر اساس متن زیر پاسخ بده و اگر داخل متن چیزی پیدا نکردی بگو نمیدونم:\n\n{context}"),
                ("human", "{input}"),
            ])
            llm = ChatOpenAI(
                model="openai/gpt-oss-120b:free",  
                temperature=0,
                api_key=env("OPENAI_API_KEY"),
                base_url="https://openrouter.ai/api/v1"
            )
            
            chain = prompt | llm

            result = chain.invoke({"context": context, "input": query})
            
            QueryAndAnswer.objects.create(query=query, awnser=result.content)
            
            return Response({"message": result.content}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class QueryAwnserListView(ListAPIView):
    queryset = QueryAndAnswer.objects.all()
    serializer_class = QueryAndAnswerSerializer