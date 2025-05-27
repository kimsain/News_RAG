"""
FastAPI 애플리케이션

이 모듈은 PGVector를 활용한 벡터 검색 API를 제공하는 FastAPI 애플리케이션입니다.
중앙화된 API 키 관리 시스템을 활용합니다.
"""

from fastapi import FastAPI, HTTPException, Depends, Body, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uvicorn
import os

from vector_db_manager import VectorDBManager
from bigkinds_api import BigkindsAPI
from config import APIConfig
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.chains import LLMChain

# OpenAI API 키 설정 (config.py에서 가져옴)
os.environ["OPENAI_API_KEY"] = APIConfig.OPENAI_API_KEY

app = FastAPI(title="벡터 데이터베이스 API", description="PGVector를 활용한 벡터 검색 API")

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 오리진 허용 (프로덕션에서는 특정 도메인으로 제한해야 함)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 설정
app.mount("/static", StaticFiles(directory="static"), name="static")

# 데이터 모델 정의
class DocumentCreate(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = None

class DocumentResponse(BaseModel):
    id: int
    content: str
    metadata: Optional[Dict[str, Any]] = None

class SearchQuery(BaseModel):
    query: str
    limit: int = Field(default=5, ge=1, le=100)

class SearchResult(BaseModel):
    id: int
    content: str
    metadata: Optional[Dict[str, Any]] = None
    similarity: float

class RAGQuery(BaseModel):
    query: str
    limit: int = Field(default=5, ge=1, le=20)

class RAGResponse(BaseModel):
    answer: str
    sources: List[SearchResult]

class NewsImportRequest(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=50)

class NewsImportResponse(BaseModel):
    success: bool
    message: str
    imported_count: int
    document_ids: List[int]

# 벡터 DB 매니저 의존성
def get_vector_db():
    db = VectorDBManager()
    try:
        db.connect()
        yield db
    finally:
        db.disconnect()

# 빅카인드 API 의존성
def get_news_api():
    return BigkindsAPI()

# LangChain 설정
def get_llm_chain():
    # RAG 프롬프트 템플릿 정의
    prompt_template = """
    다음 정보를 바탕으로 질문에 답변해주세요:
    
    정보:
    {context}
    
    질문: {question}
    
    답변:
    """
    
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )
    
    # GPT-4 모델 설정
    llm = OpenAI(model_name=APIConfig.OPENAI_COMPLETION_MODEL, temperature=0)
    
    # LLM 체인 생성
    chain = LLMChain(llm=llm, prompt=prompt)
    
    return chain

# 메인 페이지 라우트 추가
@app.get("/", response_class=HTMLResponse)
async def get_home_page():
    with open("static/index.html", "r") as f:
        return f.read()

# API 엔드포인트 정의
@app.post("/documents/", response_model=DocumentResponse, status_code=201)
def create_document(document: DocumentCreate, db: VectorDBManager = Depends(get_vector_db)):
    doc_id = db.add_document(document.content, document.metadata)
    if not doc_id:
        raise HTTPException(status_code=500, detail="문서 추가 실패")
    
    return DocumentResponse(
        id=doc_id,
        content=document.content,
        metadata=document.metadata
    )

@app.get("/documents/{doc_id}", response_model=DocumentResponse)
def get_document(doc_id: int, db: VectorDBManager = Depends(get_vector_db)):
    document = db.get_document(doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없음")
    
    return DocumentResponse(**document)

@app.delete("/documents/{doc_id}", status_code=204)
def delete_document(doc_id: int, db: VectorDBManager = Depends(get_vector_db)):
    success = db.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없음")
    
    return None

@app.post("/search/", response_model=List[SearchResult])
def search_documents(query: SearchQuery, db: VectorDBManager = Depends(get_vector_db)):
    results = db.search_similar_documents(query.query, query.limit)
    if not results:
        return []
    
    return [SearchResult(**result) for result in results]

@app.post("/rag/", response_model=RAGResponse)
def rag_query(query: RAGQuery, db: VectorDBManager = Depends(get_vector_db)):
    # 유사 문서 검색
    results = db.search_similar_documents(query.query, query.limit)
    if not results:
        raise HTTPException(status_code=404, detail="관련 문서를 찾을 수 없음")
    
    # 검색 결과를 컨텍스트로 변환
    context = "\n\n".join([f"문서 {i+1}:\n{result['content']}" for i, result in enumerate(results)])
    
    # LLM 체인 생성 및 실행
    chain = get_llm_chain()
    response = chain.run(context=context, question=query.query)
    
    return RAGResponse(
        answer=response,
        sources=[SearchResult(**result) for result in results]
    )

# 뉴스 데이터 가져오기 엔드포인트 추가
@app.post("/import-news/", response_model=NewsImportResponse)
def import_news(
    request: NewsImportRequest, 
    db: VectorDBManager = Depends(get_vector_db),
    news_api: BigkindsAPI = Depends(get_news_api)
):
    try:
        # 뉴스 데이터 가져와서 벡터 DB에 저장
        doc_ids = db.import_news_data(
            news_api=news_api,
            query=request.query,
            category=request.category,
            limit=request.limit
        )
        
        if not doc_ids:
            return NewsImportResponse(
                success=False,
                message="뉴스 데이터를 가져오지 못했습니다.",
                imported_count=0,
                document_ids=[]
            )
        
        return NewsImportResponse(
            success=True,
            message=f"{len(doc_ids)}개의 뉴스 데이터를 성공적으로 가져왔습니다.",
            imported_count=len(doc_ids),
            document_ids=doc_ids
        )
    except Exception as e:
        return NewsImportResponse(
            success=False,
            message=f"뉴스 데이터 가져오기 오류: {str(e)}",
            imported_count=0,
            document_ids=[]
        )

# 뉴스 카테고리 목록 가져오기 엔드포인트 추가
@app.get("/news-categories/")
def get_news_categories(news_api: BigkindsAPI = Depends(get_news_api)):
    try:
        categories = news_api.get_all_categories()
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"카테고리 목록 가져오기 오류: {str(e)}")

# API 상태 확인 엔드포인트
@app.get("/status/")
def get_api_status():
    return {
        "status": "online",
        "version": "1.0.0",
        "using_sample_data": APIConfig.USE_SAMPLE_DATA,
        "bigkinds_api_available": bool(APIConfig.BIGKINDS_API_KEY)
    }

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
