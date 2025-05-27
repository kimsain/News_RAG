# PGVector를 활용한 벡터 데이터베이스 구현 가이드

이 프로젝트는 PostgreSQL과 PGVector를 활용하여 벡터 데이터베이스를 구현하고, OpenAI API를 사용한 임베딩 생성 및 검색 기능을 제공합니다. 또한 FastAPI를 통한 API 서비스와 LangChain을 활용한 RAG(Retrieval-Augmented Generation) 시스템을 구현했습니다.

## 프로젝트 구조

```
vector_db_project/
├── .env                    # 환경 변수 설정 파일
├── app.py                  # FastAPI 애플리케이션
├── embedding_utils.py      # 임베딩 생성 유틸리티
├── example_client.py       # 예제 클라이언트 애플리케이션
├── requirements.txt        # 필요한 패키지 목록
├── run_server.sh           # 서버 실행 스크립트
├── test_vector_db.py       # 단위 테스트
└── vector_db_manager.py    # 벡터 데이터베이스 관리 클래스
```

## 기술 스택

- **데이터베이스**: PostgreSQL + PGVector 확장
- **임베딩 생성**: OpenAI API (text-embedding-ada-002)
- **API 서버**: FastAPI
- **RAG 구현**: LangChain + GPT-4
- **개발 언어**: Python 3.10+

## 설치 및 설정 방법

### 1. 필수 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. PostgreSQL 및 PGVector 설정

PostgreSQL을 설치하고 PGVector 확장을 활성화합니다:

```bash
# PostgreSQL 설치
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib

# PGVector 확장 설치를 위한 필수 패키지
sudo apt-get install -y git build-essential postgresql-server-dev-14

# PGVector 확장 설치
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# PostgreSQL 서비스 시작
sudo service postgresql start

# 데이터베이스 생성
sudo -u postgres psql -c "CREATE DATABASE vector_db;"

# PGVector 확장 활성화
sudo -u postgres psql -d vector_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 3. 데이터베이스 스키마 설정

```bash
sudo -u postgres psql -d vector_db -c "CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding VECTOR(1536)
);"

sudo -u postgres psql -d vector_db -c "CREATE INDEX ON documents USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);"
```

### 4. 환경 변수 설정

`.env` 파일에 OpenAI API 키를 설정합니다:

```
OPENAI_API_KEY=your_openai_api_key
```

## 주요 구성 요소

### 1. 임베딩 생성 (embedding_utils.py)

OpenAI API를 사용하여 텍스트의 임베딩 벡터를 생성합니다:

```python
def generate_embedding(text):
    """
    OpenAI API를 사용하여 텍스트의 임베딩 벡터를 생성합니다.
    
    Args:
        text (str): 임베딩할 텍스트
        
    Returns:
        list: 임베딩 벡터
    """
    try:
        response = openai.Embedding.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response['data'][0]['embedding']
    except Exception as e:
        print(f"임베딩 생성 중 오류 발생: {e}")
        return None
```

### 2. 벡터 데이터베이스 관리 (vector_db_manager.py)

PostgreSQL과 PGVector를 활용한 벡터 데이터베이스 관리 클래스:

```python
class VectorDBManager:
    """
    PostgreSQL과 pgvector를 활용한 벡터 데이터베이스 관리 클래스
    """
    
    def __init__(self, dbname="vector_db", user="postgres", password="", host="localhost", port="5432"):
        """
        데이터베이스 연결 초기화
        """
        self.conn_params = {
            "dbname": dbname,
            "user": user,
            "password": password,
            "host": host,
            "port": port
        }
        self.conn = None
        self.cursor = None
```

주요 메서드:
- `add_document(content, metadata)`: 문서 추가 및 임베딩 생성
- `search_similar_documents(query_text, limit)`: 유사 문서 검색
- `get_document(doc_id)`: 문서 조회
- `delete_document(doc_id)`: 문서 삭제

### 3. API 서버 (app.py)

FastAPI를 사용한 API 서버 구현:

```python
app = FastAPI(title="벡터 데이터베이스 API", description="PGVector를 활용한 벡터 검색 API")

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
```

주요 엔드포인트:
- `POST /documents/`: 문서 추가
- `GET /documents/{doc_id}`: 문서 조회
- `DELETE /documents/{doc_id}`: 문서 삭제
- `POST /search/`: 유사 문서 검색
- `POST /rag/`: RAG 질의 응답

### 4. RAG 구현

LangChain과 GPT-4를 활용한 RAG(Retrieval-Augmented Generation) 구현:

```python
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
    llm = OpenAI(model_name="gpt-4", temperature=0)
    
    # LLM 체인 생성
    chain = LLMChain(llm=llm, prompt=prompt)
    
    return chain
```

## 사용 방법

### 1. 서버 실행

```bash
./run_server.sh
```

또는

```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

### 2. API 문서 확인

브라우저에서 `http://localhost:8000/docs`에 접속하여 API 문서를 확인할 수 있습니다.

### 3. 예제 클라이언트 실행

```bash
python example_client.py
```

예제 클라이언트는 다음 기능을 시연합니다:
- 샘플 문서 추가
- 벡터 검색
- RAG 질의
- 문서 삭제

### 4. 단위 테스트 실행

```bash
python test_vector_db.py
```

## 확장 및 개선 방향

1. **인증 및 권한 관리**: JWT 또는 OAuth2를 통한 API 인증 추가
2. **벡터 인덱스 최적화**: 데이터 증가에 따른 인덱스 재구성 및 최적화
3. **분산 처리**: 대용량 데이터 처리를 위한 분산 시스템 구현
4. **캐싱 레이어**: 자주 사용되는 쿼리 결과 캐싱
5. **모니터링 및 로깅**: 시스템 성능 및 사용량 모니터링

## 결론

이 프로젝트는 PostgreSQL과 PGVector를 활용하여 벡터 데이터베이스를 구현하고, OpenAI API를 사용한 임베딩 생성 및 검색 기능을 제공합니다. FastAPI를 통한 API 서비스와 LangChain을 활용한 RAG 시스템을 구현하여 인구 정책 관련 정보 검색 및 질의응답 서비스를 제공할 수 있습니다.

이 구현은 확장성과 유연성을 고려하여 설계되었으며, 다양한 도메인에 적용할 수 있습니다. 특히 대규모 텍스트 데이터에서 의미적 검색이 필요한 애플리케이션에 적합합니다.