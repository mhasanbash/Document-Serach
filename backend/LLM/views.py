from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status, permissions

from .serializers import QuerySerializer, DocumentsSerializer, DocumentsUpdateSerializer, QueryAndAnswerSerializer
from .models import Documents, QueryAndAnswer

from langchain.chat_models import init_chat_model
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI


from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains import create_retrieval_chain, LLMChain

from langchain_core.prompts import ChatPromptTemplate


from langchain_chroma import Chroma
from rest_framework.response import Response
from langchain_kreuzberg import KreuzbergLoader

from langchain_community.vectorstores.utils import filter_complex_metadata

from rest_framework.generics import (
    RetrieveAPIView, 
    RetrieveUpdateAPIView, 
    ListAPIView, 
    CreateAPIView, 
    UpdateAPIView
)
from rest_framework.parsers import MultiPartParser, FormParser

import os
import shutil

from django.conf import settings

from django.shortcuts import get_object_or_404

import tempfile

import environ

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

class ChromaService:
    def __init__(self):
        self.persist_directory = settings.CHROMA_PERSIST_DIR
        # Embedding Function جدید
        self.embedding_function = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=env("OPENAI_API_KEY"),
                base_url="https://openrouter.ai/api/v1"
            )
        
    def _get_loader(self, file_path):
        return KreuzbergLoader(file_path=file_path)
        
    def index_document(self, document_instance):
        collection_name = f"doc_{document_instance.id}"
        
        loader = self._get_loader(document_instance.uploaded_file.path)
        raw_docs = (loader.load())
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(raw_docs)
        chunks = [chunk.page_content for chunk in chunks]

        vector_store = Chroma.from_texts(
            texts=chunks,
            embedding=self.embedding_function,
            persist_directory=self.persist_directory,
            collection_name=collection_name
        )
        collection_uuid = vector_store._client.get_collection(collection_name).id
        document_instance.chroma_uuid = str(collection_uuid)
        document_instance.is_processed = True
        document_instance.raw_text = raw_docs[0].page_content
        document_instance.save()
        
    def delete_document(self, document_instance):
        collection_name = f"doc_{document_instance.id}"
        vector_store = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_function,
            collection_name=collection_name
        )
        vector_store.delete_collection()
        
        # collection_path = os.path.join(self.persist_directory, document_instance.chroma_uuid)
        # if os.path.exists(collection_path) and os.path.isdir(collection_path):
        #     shutil.rmtree(collection_path)
        #     print(f"Deleted folder: {collection_path}")
        
    def search_across_documents(self, query_text, k_per_doc=3, max_total=4):
        all_results = []
        documents = Documents.objects.filter(is_processed=True)
        
        for doc in documents:
            collection_name = f"doc_{doc.id}"
            try:
                vector_store = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embedding_function,
                    collection_name=collection_name
                )
                results = vector_store.similarity_search_with_score(query_text, k=k_per_doc)
                for doc_chunk, score in results:
                    all_results.append({
                        "content": doc_chunk.page_content,
                        "doc_title": doc.title,
                        "doc_id": doc.id,
                        "score": score,
                        "collection_name":collection_name
                    })
            except Exception as e:
                print(f"Error searching collection {collection_name}: {e}")
                continue
        
        all_results.sort(key=lambda x: x["score"])
        
        all_results.sort(key=lambda x: x["score"])
        return all_results[:max_total]
        
       
        
    
class DocumentAddView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        print(f"data : {data['uploaded_file']}")
        print(f"data name : {data['uploaded_file'].name}")
        
        if 'uploaded_file' in data:
            data['title'] = data['uploaded_file'].name 
            
        print(f"data after : {data['uploaded_file']}")
        
        serializer = DocumentsSerializer(data=data)
        
        if serializer.is_valid():
            document = serializer.save()
            ChromaService().index_document(document)
            
            return Response({"message": "فایل با موفقیت آپلود و پردازش شد"}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
           
class DocumentDeleteView(APIView):
    def delete(self, request, *args, **kwargs):
        print(f"before title")
        title = kwargs.get('title')
        print(f"title : {title}")
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
        
        
        # current_dir = os.path.dirname(os.path.abspath(__file__))
        # file_path = os.path.join(current_dir, "sample.docx")
    
        
        # if not os.path.exists(file_path):
        #     return Response(
        #         {"error": f"فایل '{file_path}' پیدا نشد. مسیر مطلق یا صحیح را وارد کنید."},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )
        

        try:
            # loader = KreuzbergLoader(file_path=file_path)
            # raw_docs = loader.load()
            
            # text_splitter = RecursiveCharacterTextSplitter(
            #     chunk_size=1000,
            #     chunk_overlap=200,
            #     separators=["\n\n", "\n", " ", ""]
            # )

            # chunks = text_splitter.split_documents(raw_docs)
            # KEYS_TO_REMOVE = ['boundaries', 'pages', 'total_count', 'unit_type', 'page_number', 
            #       'bbox', 'coordinates', 'page', 'rect', 'block']
            
            # for chunk in chunks:
            #     metadata = chunk.metadata
            #     for key in KEYS_TO_REMOVE:
            #         metadata.pop(key, None)
            #     chunk.metadata = {k: v for k, v in metadata.items() 
            #                     if isinstance(v, (str, int, float, bool, list, type(None)))}
            # print(chunks)
                
            # print("embedding")
            
            # embeddings = OpenAIEmbeddings(
            #     model="text-embedding-3-small",
            #     api_key="",
            #     base_url="https://openrouter.ai/api/v1"
            # )
            
            # print("vectoring")
            
            # vectorstore = Chroma.from_documents(
            #     documents=chunks,
            #     embedding=embeddings,
            #     # persist_directory="./chroma"
            # )
            
            # print("retrievering")
            # retriever = vectorstore.as_retriever(
            #     search_type="similarity",  
            #     search_kwargs={"k": 4}     
            # )
            
            # print("model")
            # prompt = ChatPromptTemplate.from_messages([
            #     ("system", "تو یک دستیار دلقک و مخالف خودرو خارجی و دروغگو هستی. به سوال بر اساس متن زیر پاسخ بده:\n\n{context}"),
            #     ("human", "{input}"),
            # ])
            # llm = ChatOpenAI(
            #     model="openai/gpt-oss-120b:free",  
            #     temperature=0,
            #     api_key="",
            #     base_url="https://openrouter.ai/api/v1"
            # )
            
            # combine_docs_chain = create_stuff_documents_chain(llm, prompt)
            
            # print("before chainig")
            
            # rag_chain = create_retrieval_chain(retriever, combine_docs_chain)
            
            # print(f"before result - rag chain : {rag_chain}")

            # result = rag_chain.invoke({"input": query})
            
            chroma_service = ChromaService()
            top_results = chroma_service.search_across_documents(query, k_per_doc=2, max_total=6)
            
            print(f"top_results after sort : {top_results}")
            
            context_parts = []
            for idx, res in enumerate(top_results, 1):
                context_parts.append(f"[doc {idx} - {res['doc_title']}]:\n{res['content']}")
            context = "\n\n".join(context_parts)
            
            print(f"context_parts after create : {context}")

            
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
            
            print("before create chain")
            
            chain = prompt | llm
            
            print("after create chain before invole")

            result = chain.invoke({"context": context, "input": query})
            
            print(f"result is : {result}")
            
            QueryAndAnswer.objects.create(query=query, awnser=result.content)
            
            return Response({"message": result.content}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class QueryAwnserListView(ListAPIView):
    queryset = QueryAndAnswer.objects.all()
    serializer_class = QueryAndAnswerSerializer