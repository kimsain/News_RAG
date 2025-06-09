"""
LangChain 기반 FastAPI 애플리케이션

이 모듈은 LangChain의 PGVector와 OpenAIEmbeddings를 활용한 벡터 검색 API를 제공하는 FastAPI 애플리케이션입니다.
"""

from fastapi import FastAPI, HTTPException, Depends, Body, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uvicorn
import os

# LangChain 기반 모듈 import
from langchain_vector_db_manager import LangChainVectorDBManager
from bigkinds_api import BigkindsAPI
from config import APIConfig
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.chains import LLMChain

# OpenAI API 키 설정
os.environ["OPENAI_API_KEY"] = APIConfig.OPENAI_API_KEY

app = FastAPI(title="LangChain 벡터 데이터베이스 API", description="LangChain PGVector를 활용한 벡터 검색 API")

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 설정 (선택적)
# app.mount("/static", StaticFiles(directory="static"), name="static")

# 데이터 모델 정의
class DocumentCreate(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = None
    use_splitter: bool = Field(default=False, description="텍스트 분할 사용 여부")

class DocumentResponse(BaseModel):
    ids: List[str]
    content: str
    metadata: Optional[Dict[str, Any]] = None

class SearchQuery(BaseModel):
    query: str
    limit: int = Field(default=5, ge=1, le=100)
    score_threshold: Optional[float] = Field(default=None, description="유사도 임계값")

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
    use_splitter: bool = Field(default=False, description="텍스트 분할 사용 여부")

class NewsImportResponse(BaseModel):
    success: bool
    message: str
    imported_count: int
    document_ids: List[str]

# 벡터 DB 매니저 의존성 (LangChain 기반)
def get_vector_db():
    return LangChainVectorDBManager()

# 빅카인드 API 의존성
def get_news_api():
    return BigkindsAPI()

# LangChain 설정
def get_llm_chain():
    """
    RAG를 위한 LangChain LLM 체인 생성
    """
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
    
    # GPT 모델 설정
    llm = OpenAI(
        model_name=APIConfig.OPENAI_COMPLETION_MODEL, 
        temperature=0,
        openai_api_key=APIConfig.OPENAI_API_KEY
    )
    
    # LLM 체인 생성
    chain = LLMChain(llm=llm, prompt=prompt)
    
    return chain

# API 엔드포인트 정의
@app.get("/")
async def get_home():
    """홈페이지"""
    return {
        "message": "LangChain 기반 벡터 데이터베이스 API",
        "version": "1.0.0",
        "features": [
            "LangChain OpenAIEmbeddings",
            "LangChain PGVector",
            "LangChain RecursiveCharacterTextSplitter",
            "RAG (Retrieval-Augmented Generation)"
        ]
    }

@app.post("/documents/", response_model=DocumentResponse, status_code=201)
def create_document(document: DocumentCreate, db: LangChainVectorDBManager = Depends(get_vector_db)):
    """문서 추가"""
    doc_ids = db.add_document(
        content=document.content, 
        metadata=document.metadata,
        use_splitter=document.use_splitter
    )
    
    if not doc_ids:
        raise HTTPException(status_code=500, detail="문서 추가 실패")
    
    return DocumentResponse(
        ids=doc_ids,
        content=document.content,
        metadata=document.metadata
    )

@app.post("/search/", response_model=List[SearchResult])
def search_documents(query: SearchQuery, db: LangChainVectorDBManager = Depends(get_vector_db)):
    """유사 문서 검색"""
    results = db.search_similar_documents(
        query_text=query.query, 
        limit=query.limit,
        score_threshold=query.score_threshold
    )
    
    if not results:
        return []
    
    return [SearchResult(**result) for result in results]

@app.post("/rag/", response_model=RAGResponse)
def rag_query(query: RAGQuery, db: LangChainVectorDBManager = Depends(get_vector_db)):
    """RAG 기반 질의응답"""
    # 유사 문서 검색
    results = db.search_similar_documents(query.query, query.limit)
    if not results:
        raise HTTPException(status_code=404, detail="관련 문서를 찾을 수 없음")
    
    # 검색 결과를 컨텍스트로 변환
    context = "\n\n".join([
        f"문서 {i+1}:\n{result['content']}" 
        for i, result in enumerate(results)
    ])
    
    # LLM 체인 생성 및 실행
    chain = get_llm_chain()
    response = chain.run(context=context, question=query.query)
    
    return RAGResponse(
        answer=response,
        sources=[SearchResult(**result) for result in results]
    )

@app.post("/import-news/", response_model=NewsImportResponse)
def import_news(
    request: NewsImportRequest, 
    db: LangChainVectorDBManager = Depends(get_vector_db),
    news_api: BigkindsAPI = Depends(get_news_api)
):
    """뉴스 데이터 가져오기 및 벡터 DB 저장"""
    try:
        # 뉴스 데이터 가져와서 벡터 DB에 저장
        doc_ids = db.import_news_data(
            news_api=news_api,
            query=request.query,
            category=request.category,
            limit=request.limit,
            use_splitter=request.use_splitter
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
            document_ids=[str(doc_id) for doc_id in doc_ids]
        )
    except Exception as e:
        return NewsImportResponse(
            success=False,
            message=f"뉴스 데이터 가져오기 오류: {str(e)}",
            imported_count=0,
            document_ids=[]
        )

@app.get("/news-categories/")
def get_news_categories(news_api: BigkindsAPI = Depends(get_news_api)):
    """뉴스 카테고리 목록 조회"""
    try:
        categories = news_api.get_all_categories()
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"카테고리 목록 가져오기 오류: {str(e)}")

@app.delete("/collection/", status_code=204)
def delete_collection(db: LangChainVectorDBManager = Depends(get_vector_db)):
    """전체 컬렉션 삭제"""
    success = db.delete_collection()
    if not success:
        raise HTTPException(status_code=500, detail="컬렉션 삭제 실패")
    return None

@app.get("/status/")
def get_api_status():
    """API 상태 확인"""
    return {
        "status": "online",
        "version": "1.0.0 (LangChain)",
        "framework": "LangChain",
        "components": {
            "embeddings": "LangChain OpenAIEmbeddings",
            "vectorstore": "LangChain PGVector",
            "text_splitter": "LangChain RecursiveCharacterTextSplitter",
            "llm": "LangChain OpenAI"
        },
        "using_sample_data": APIConfig.USE_SAMPLE_DATA,
        "bigkinds_api_available": bool(APIConfig.BIGKINDS_API_KEY)
    }

if __name__ == "__main__":
    uvicorn.run("langchain_app:app", host="0.0.0.0", port=8000, reload=True)

