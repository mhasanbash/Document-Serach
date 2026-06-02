import environ

from django.conf import settings
from .models import Documents

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_kreuzberg import KreuzbergLoader


env = environ.Env()
environ.Env.read_env(settings.BASE_DIR / ".env")


class ChromaService:
    def __init__(self):
        self.persist_directory = settings.CHROMA_PERSIST_DIR
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