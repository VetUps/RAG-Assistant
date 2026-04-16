import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

from typing import List, Optional
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import uvicorn
import tempfile
import time
from contextlib import asynccontextmanager

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import Qdrant
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_gigachat import GigaChat, GigaChatEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, VectorParams

import parser


load_dotenv()


class SearchRequest(BaseModel):
    query: str
    # limit: Optional[int] = 3
    role: str # программист, студент, глава
    chat_history: List[dict] = Field(default_factory=list) #[{"human": "текст"}, {"ai": "текст"}, ..., ...]


class SearchResponse(BaseModel):
    answer: str
    sources: List[str]
    processing_time: float


class DocumentUploadResponse(BaseModel):
    message: str
    chunks_created: int
    document_name: str


class DocumentSummary(BaseModel):
    name: str
    chunks_count: int


class DocumentsByRoleResponse(BaseModel):
    role: str
    total_documents: int
    total_chunks: int
    documents: List[DocumentSummary]


class HealthResponse(BaseModel):
    status: str
    qdrant_connected: bool
    models_loaded: bool
    total_chunks: int
    details: List[str] = Field(default_factory=list)


giga_emb = None
embedding_model = None
vectorstore = None
rag_chain = None
contextualize_chain = None
llm = None
retriever = None
prompt_template = None
qdrant_client = None

GIGA_EMB_PATH = "ai-sage/Giga-Embeddings-instruct"
CASHE_FOLDER_PATH = r"models"
GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS", "")
GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
GIGACHAT_MODEL = os.getenv("GIGACHAT_MODEL", "GigaChat-2")
GIGACHAT_EMBEDDING_MODEL = os.getenv("GIGACHAT_EMBEDDING_MODEL", "Embeddings")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "rag_collection")
VECTOR_SIZE = int(os.getenv("QDRANT_VECTOR_SIZE", "1024"))
ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".docx", ".txt"}
ALLOWED_ROLES = {"студент", "программист", "глава"}
MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(25 * 1024 * 1024)))
UPLOAD_CHUNK_SIZE_BYTES = 1024 * 1024
SCORE_THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0.5"))
CORS_ALLOW_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]


# class SentenceTransformerEmbeddings(Embeddings):
#     def __init__(self, model: SentenceTransformer, batch_size: int = 32):
#         self.model = model
#         self.batch_size = batch_size

#     def embed_documents(self, texts: List[str]) -> List[List[float]]:
#         embs = self.model.encode(texts, batch_size=self.batch_size, show_progress_bar=False)
#         return [emb.tolist() for emb in embs]

#     def embed_query(self, text: str) -> List[float]:
#         emb = self.model.encode([text], show_progress_bar=False)[0]
#         return emb.tolist()


# def load_embedding_model():
#     print("Загрузка SentenceTransformer...")
#     os.environ["TRANSFORMERS_VERBOSITY"] = "error"
#     return SentenceTransformer(
#         GIGA_EMB_PATH,
#         trust_remote_code=True,
#         device="cpu",
#         cache_folder=CASHE_FOLDER_PATH
#     )


def get_gigachat_credentials() -> str:
    if not GIGACHAT_CREDENTIALS:
        raise RuntimeError("GIGACHAT_CREDENTIALS не задан в переменных окружения")

    return GIGACHAT_CREDENTIALS


def load_llm():
    print("Инициализация GigaChat через langchain-gigachat...")
    return GigaChat(
        credentials=get_gigachat_credentials(),
        model=GIGACHAT_MODEL,
        timeout=60,
        verify_ssl_certs=False,
        temperature=0.1,
        max_tokens=256,
        scope=GIGACHAT_SCOPE
    )


def get_or_create_qdrant_client() -> QdrantClient:
    global qdrant_client

    if qdrant_client is None:
        qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    return qdrant_client


def get_collection_vector_size(collection_info) -> Optional[int]:
    vectors = getattr(getattr(collection_info, "config", None), "params", None)
    vectors = getattr(vectors, "vectors", None)

    if isinstance(vectors, dict):
        first_vector = next(iter(vectors.values()), None)
        return getattr(first_vector, "size", None)

    return getattr(vectors, "size", None)


def ensure_qdrant_collection() -> None:
    client = get_or_create_qdrant_client()

    if not client.collection_exists(QDRANT_COLLECTION_NAME):
        print(f"Коллекция Qdrant '{QDRANT_COLLECTION_NAME}' не найдена, создаю...")
        client.create_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )
        print(f"Коллекция Qdrant '{QDRANT_COLLECTION_NAME}' создана")
        return

    collection_info = client.get_collection(QDRANT_COLLECTION_NAME)
    existing_size = get_collection_vector_size(collection_info)
    if existing_size and existing_size != VECTOR_SIZE:
        points_count = client.count(QDRANT_COLLECTION_NAME, exact=True).count
        if points_count == 0:
            print(
                f"Пустая коллекция Qdrant '{QDRANT_COLLECTION_NAME}' имеет размер вектора {existing_size}, "
                f"ожидается {VECTOR_SIZE}. Пересоздаю коллекцию..."
            )
            client.delete_collection(QDRANT_COLLECTION_NAME)
            client.create_collection(
                collection_name=QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
            )
            print(f"Коллекция Qdrant '{QDRANT_COLLECTION_NAME}' пересоздана")
            return

        raise RuntimeError(
            f"Коллекция Qdrant '{QDRANT_COLLECTION_NAME}' имеет размер вектора {existing_size}, "
            f"а приложение ожидает {VECTOR_SIZE}. В коллекции уже есть точки: {points_count}. "
            "Создайте новую коллекцию через QDRANT_COLLECTION_NAME или вручную удалите старую, если данные не нужны."
        )


def build_role_filter(role: str) -> Filter:
    return Filter(
        must=[
            FieldCondition(
                key="metadata.category",
                match=MatchValue(value=role)
            )
        ]
    )


def document_from_qdrant_point(point) -> Document:
    payload = point.payload or {}
    metadata = payload.get("metadata") or {}
    content = payload.get("text") or payload.get("page_content") or ""

    return Document(page_content=content, metadata=metadata)


def similarity_search_with_score(query: str, role: str, k: int = 10) -> list[tuple[Document, float]]:
    query_embedding = embedding_model.embed_query(query)
    if len(query_embedding) != VECTOR_SIZE:
        raise RuntimeError(
            f"Модель эмбеддингов вернула вектор размерности {len(query_embedding)}, "
            f"а Qdrant настроен на {VECTOR_SIZE}. Проверьте QDRANT_VECTOR_SIZE."
        )

    response = get_or_create_qdrant_client().query_points(
        collection_name=QDRANT_COLLECTION_NAME,
        query=query_embedding,
        query_filter=build_role_filter(role),
        limit=k,
        with_payload=True,
        with_vectors=False,
    )

    return [
        (document_from_qdrant_point(point), point.score)
        for point in response.points
    ]


def count_indexed_chunks(role: Optional[str] = None) -> int:
    client = get_or_create_qdrant_client()
    count_filter = build_role_filter(role) if role else None

    return client.count(
        collection_name=QDRANT_COLLECTION_NAME,
        count_filter=count_filter,
        exact=True
    ).count


def list_documents_by_role(role: str) -> DocumentsByRoleResponse:
    validate_role(role)
    ensure_qdrant_collection()

    documents: dict[str, int] = {}
    next_offset = None

    while True:
        points, next_offset = get_or_create_qdrant_client().scroll(
            collection_name=QDRANT_COLLECTION_NAME,
            scroll_filter=build_role_filter(role),
            limit=256,
            offset=next_offset,
            with_payload=True,
            with_vectors=False,
        )

        for point in points:
            payload = point.payload or {}
            metadata = payload.get("metadata") or {}
            source = metadata.get("source")
            if source:
                documents[source] = documents.get(source, 0) + 1

        if next_offset is None:
            break

    summaries = [
        DocumentSummary(name=name, chunks_count=chunks_count)
        for name, chunks_count in sorted(documents.items(), key=lambda item: item[0].lower())
    ]

    return DocumentsByRoleResponse(
        role=role,
        total_documents=len(summaries),
        total_chunks=sum(item.chunks_count for item in summaries),
        documents=summaries
    )


def validate_role(role: str) -> None:
    if role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=422,
            detail=f"Неподдерживаемая роль. Доступные роли: {', '.join(sorted(ALLOWED_ROLES))}"
        )


def validate_search_request(request: SearchRequest) -> None:
    validate_role(request.role)

    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Запрос не должен быть пустым")


def ensure_runtime_ready(require_embeddings: bool = False, require_llm: bool = False) -> None:
    try:
        ensure_qdrant_collection()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Qdrant недоступен или не готов: {str(e)}")

    if not vectorstore:
        raise HTTPException(status_code=503, detail="Векторное хранилище не инициализировано")

    if require_embeddings and not embedding_model:
        raise HTTPException(status_code=503, detail="Модель эмбеддингов не загружена")

    if require_llm and not llm:
        raise HTTPException(status_code=503, detail="LLM не инициализирована")


def raise_friendly_external_error(error: Exception) -> None:
    message = str(error)
    if "status\":402" in message or "Payment Required" in message or " 402 " in message:
        raise HTTPException(
            status_code=402,
            detail=(
                "GigaChat вернул 402 Payment Required. Проверьте, подключён ли пакет Embeddings "
                "для загрузки документов или доступный пакет генерации для ответов."
            )
        )

    raise HTTPException(status_code=500, detail=f"Ошибка внешнего API: {message}")


def create_parent_child_chunks(documents, parent_chunk_size=1000, child_chunk_size=350):
    print("НАЧАЛО ЧАНКОВАНИЯ")
    parent_splitter = RecursiveCharacterTextSplitter(
        chunk_size=parent_chunk_size,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    parent_chunks = parent_splitter.split_documents(documents)

    child_splitter = RecursiveCharacterTextSplitter(
        chunk_size=child_chunk_size,
        chunk_overlap=50,
        separators=[".", ". ", " .", "?", "!"]
    )

    child_chunks = []
    for i, parent in enumerate(parent_chunks):
        children = child_splitter.split_documents([parent])
        for child in children:
            child.metadata["parent_id"] = f"parent_{i}"
            child.metadata["parent_content"] = parent.page_content
            child_chunks.append(child)

    return parent_chunks, child_chunks


def validate_upload_metadata(role: str, filename: Optional[str]) -> tuple[str, str]:
    validate_role(role)

    safe_filename = Path(filename or "").name
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Имя файла отсутствует")

    extension = Path(safe_filename).suffix.lower()
    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_UPLOAD_EXTENSIONS))
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат файла. Разрешены: {allowed}"
        )

    return safe_filename, extension


async def save_upload_to_temp_file(file: UploadFile, extension: str) -> tuple[str, int]:
    bytes_written = 0
    tmp_path = ""

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
            tmp_path = tmp_file.name

            while chunk := await file.read(UPLOAD_CHUNK_SIZE_BYTES):
                bytes_written += len(chunk)
                if bytes_written > MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Файл слишком большой. Максимальный размер: {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} МБ"
                    )
                tmp_file.write(chunk)

        if bytes_written == 0:
            raise HTTPException(status_code=400, detail="Файл пустой")

        return tmp_path, bytes_written
    except Exception:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def initialize_contextualize_chain():
    global contextualize_chain

    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", """
                Учитывая историю чата и последний вопрос пользователя который может ссылаться на контекст в истории чата 
                сформулируйте отдельный вопрос, который можно понять без истории чата. НЕ отвечайте на вопрос
                просто переформулируйте его, если это необходимо, а в противном случае верните как есть.
        """),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    contextualize_chain = contextualize_q_prompt | llm | StrOutputParser()

    print("Цепочка для контекстуализация запроса готова!")

def initialize_rag_chain():
    global giga_emb, embedding_model, vectorstore, rag_chain, llm, retriever, prompt_template

    # print("Инициализация моделей...")
    # giga_emb = load_embedding_model()
    # embedding_model = SentenceTransformerEmbeddings(giga_emb)

    embedding_model = GigaChatEmbeddings(
        credentials=get_gigachat_credentials(),
        verify_ssl_certs=False,
        scope=GIGACHAT_SCOPE,
        model=GIGACHAT_EMBEDDING_MODEL,
    )
    
    llm = load_llm()

    print("Подключение к Qdrant...")
    ensure_qdrant_collection()

    # LangChain обёртка
    vectorstore = Qdrant(
        client=get_or_create_qdrant_client(),
        collection_name=QDRANT_COLLECTION_NAME,
        embeddings=embedding_model,
        content_payload_key="text",
        metadata_payload_key="metadata"
    )



    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """Ты — {role}. Отвечай кратко ТОЛЬКО на основе предоставленного контекста.

                       КОНТЕКСТ:
                       {context}"""),
        ("human", "Вопрос: {input}")
    ])

    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    rag_chain = True

    initialize_contextualize_chain()
    
    print("RAG система готова к работе!")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        initialize_rag_chain()
    except Exception as e:
        print(f"RAG система не инициализирована: {str(e)}")
    yield


app = FastAPI(title="RAG Assistant API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
async def health_check():
    details = []

    try:
        ensure_qdrant_collection()
        qdrant_connected = True
        total_chunks = count_indexed_chunks()
    except Exception as e:
        details.append(f"Qdrant: {str(e)}")
        qdrant_connected = False
        total_chunks = 0

    models_loaded = all([embedding_model, llm, vectorstore, rag_chain])
    if not GIGACHAT_CREDENTIALS:
        details.append("GIGACHAT_CREDENTIALS не задан")
    if not embedding_model:
        details.append("Модель эмбеддингов не инициализирована")
    if not llm:
        details.append("LLM не инициализирована")
    if not vectorstore:
        details.append("Векторное хранилище не инициализировано")

    return HealthResponse(
        status="healthy" if qdrant_connected and models_loaded else "error",
        qdrant_connected=qdrant_connected,
        models_loaded=models_loaded,
        total_chunks=total_chunks,
        details=details
    )


@app.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    try:
        start_time = time.time()
        validate_search_request(request)
        ensure_runtime_ready(require_embeddings=True, require_llm=True)

        role_chunks_count = count_indexed_chunks(request.role)
        if role_chunks_count == 0:
            return SearchResponse(
                answer="В базе знаний пока нет документов для выбранной роли.",
                sources=["Нет"],
                processing_time=round(time.time() - start_time, 2)
            )

        chat_history = []
        for msg in request.chat_history:
            role = msg.get("role", "").lower()
            content = msg.get("content", "")

            if role in ("user", "human"):
                chat_history.append(("human", content))
            elif role in ("assistant", "ai"):
                chat_history.append(("ai", content))

        llm_query = request.query.strip()
        print(f"Запрос: {llm_query}")

        child_docs_with_score = similarity_search_with_score(
            llm_query,
            role=request.role,
            k=10
        )

        filtered_child = [(doc, score) for doc, score in child_docs_with_score if score >= SCORE_THRESHOLD]

        if not filtered_child and chat_history and contextualize_chain:
            llm_query = contextualize_chain.invoke({
                "input": request.query,
                "chat_history": chat_history
            }).strip()
            print(f"Контекстуализированный запрос: {llm_query}")
            child_docs_with_score = similarity_search_with_score(
                llm_query,
                role=request.role,
                k=10
            )
            filtered_child = [(doc, score) for doc, score in child_docs_with_score if score >= SCORE_THRESHOLD]

        for doc, score in child_docs_with_score:
            print("=" * 50)
            print(f"Score - {score}\n\n")
            print(f"Найденный контекст: {doc.page_content}")
            print("=" * 50)

        filtered_child_docs = [doc for doc, _ in filtered_child]

        parent_contents = set()
        sources = set()
        for child in filtered_child_docs:
            parent_content = child.metadata.get("parent_content")
            if parent_content:
                parent_contents.add(parent_content)
            sources.add(child.metadata.get("source", "unknown"))

        context = "\n\n".join(parent_contents) if parent_contents else "Нет релевантных документов."
        if context == "Нет релевантных документов.":
            return SearchResponse(
                answer="Я не знаю ответа на этот вопрос, так как в предоставленном контексте нет информации.",
                sources=["Нет"],
                processing_time=round(time.time() - start_time, 2)
            )

        user_role = ""
        match request.role:
            case 'студент':
                user_role = "ассистент для студента технического ВУЗа"
            case 'программист':
                user_role = "ассистент для программиста технического ВУЗа"
            case 'глава':
                user_role = "ассистент для главы сельского поселения"

        full_messaages = [("system", f"""Ты — {user_role}. Отвечай кратко ТОЛЬКО на основе предоставленного контекста.\n\n
                                       КОНТЕКСТ:{context}""")]

        full_messaages.extend(chat_history)
        full_messaages.append(("human", request.query))

        print(full_messaages)

        answer = llm.invoke(full_messaages).content

        processing_time = time.time() - start_time

        return SearchResponse(
            answer=answer,
            sources=list(sources) if sources else ["Нет"],
            processing_time=round(processing_time, 2)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise_friendly_external_error(e)


@app.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(role: str = Form(...), file: UploadFile = File(...)):
    tmp_path = ""

    try:
        safe_filename, extension = validate_upload_metadata(role, file.filename)
        ensure_runtime_ready(require_embeddings=True)

        print(f"Начало обработки файла: {safe_filename}")

        tmp_path, bytes_written = await save_upload_to_temp_file(file, extension)
        print(f"Файл сохранён во временное хранилище, размер: {bytes_written} байт")

        print("Парсинг документа...")
        try:
            content = parser.parse_document(tmp_path)
        except (FileNotFoundError, ValueError) as e:
            raise HTTPException(status_code=400, detail=str(e))

        if not content or not content.strip():
            raise HTTPException(status_code=400, detail="Не удалось извлечь текст из документа")

        print(f"Документ распарсен, длина: {len(content)} символов")

        doc = Document(
            page_content=content,
            metadata={"source": safe_filename, "category": role}
        )

        print("Разбиение на чанки...")
        parent_chunks, child_chunks = create_parent_child_chunks([doc])
        if not child_chunks:
            raise HTTPException(status_code=400, detail="Документ не содержит текста для индексации")

        print(f"Создано дочерних чанков: {len(child_chunks)}")
        print(f"Создано родительских чанков: {len(parent_chunks)}")

        print("Добавление в векторную базу...")
        vectorstore.add_documents(child_chunks)
        print("Чанки успешно добавлены")

        return DocumentUploadResponse(
            message="Документ успешно обработан и добавлен в базу знаний",
            chunks_created=len(child_chunks),
            document_name=safe_filename
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка при обработке документа: {str(e)}")
        raise_friendly_external_error(e)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        await file.close()


@app.get("/documents/count")
async def get_documents_count():
    try:
        ensure_qdrant_collection()
        count = count_indexed_chunks()
        return {"total_chunks": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")


@app.get("/documents", response_model=DocumentsByRoleResponse)
async def get_documents_by_role(role: str = Query(...)):
    try:
        return list_documents_by_role(role)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка документов: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "rag_api_qu:app",
        host="127.0.0.1",
        port=8000,
        reload=False
    )
