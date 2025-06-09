# News Semantic Search
이 프로젝트는 뉴스 기사의 임베딩과 시멘틱 서치 기능을 구현한 FastAPI 애플리케이션입니다.

## 프로젝트 발전 과정

### 1단계: MVP 개발 (LangChain 기반)
빠른 프로토타이핑을 위해 LangChain의 다양한 모듈을 활용하여 핵심 기능을 구현했습니다.

### 2단계: 최적화 (직접 구현)
LLM 모델이 확정되고 성능 최적화가 필요해지면서 일부 컴포넌트를 직접 구현으로 전환했습니다.
- 임베딩: `openai.Embedding.create()` 직접 호출
- 벡터 DB: `psycopg2`로 PostgreSQL 직접 관리
- 텍스트 처리: 단순 문자열 결합(BigKind API에서 뉴스 데이터가 제목과 본문 몇줄만 제공됨)

## 주요 기능

### LangChain 컴포넌트
- **OpenAIEmbeddings**: 텍스트 임베딩 생성
- **PGVector**: PostgreSQL 기반 벡터 데이터베이스
- **RecursiveCharacterTextSplitter**: 텍스트 청크 분할
- **LLMChain**: RAG 기반 질의응답

### 핵심 기능
1. **문서 임베딩**: 뉴스 기사를 벡터로 변환하여 저장
2. **시멘틱 서치**: 의미 기반 유사 문서 검색
3. **RAG (Retrieval-Augmented Generation)**: 검색된 문서를 기반으로 한 질의응답
4. **텍스트 분할**: 긴 문서를 적절한 크기로 분할 (선택적)

## 파일 구조

```
langchain/
├── langchain_app.py                    # LangChain 기반 FastAPI 메인 애플리케이션
├── langchain_vector_db_manager.py      # LangChain PGVector 벡터 DB 관리
├── langchain_embedding_utils.py        # LangChain OpenAIEmbeddings 유틸리티
├── langchain_text_splitter.py          # LangChain RecursiveCharacterTextSplitter
├── bigkinds_api.py                     # 뉴스 API
├── requirements.txt                    # 필요한 패키지 목록
└── README.md                           # ReadMe
```

### 최적화 구현 (기존 파일들)
```
News_RAG/
├── app.py                              # 최적화된 FastAPI 애플리케이션 (LangChain LLM만 사용)
├── vector_db_manager.py                # psycopg2 직접 사용한 벡터 DB 관리
├── embedding_utils.py                  # openai 라이브러리 직접 호출
├── bigkinds_api.py                     # 뉴스 API (공통)
├── sample_data.py                      # 샘플 데이터 생성
├── example_client.py                   # 클라이언트 예시
├── setup_db.sh                         # 데이터베이스 설정 스크립트
├── run_server.sh                       # 서버 실행 스크립트
├── run_test.sh                         # 테스트 스크립트
├── requirements.txt                    # 패키지 목록
```

### 주요 차이점

| 파일 | LangChain MVP | 최적화 버전 | 주요 차이점 |
|------|---------------|-------------|-------------|
| **메인 앱** | `langchain_app.py` | `app.py` | LangChain 컴포넌트 vs 직접 구현 |
| **벡터 DB** | `langchain_vector_db_manager.py` | `vector_db_manager.py` | PGVector vs psycopg2 직접 사용 |
| **임베딩** | `langchain_embedding_utils.py` | `embedding_utils.py` | OpenAIEmbeddings vs openai.Embedding.create() |
| **텍스트 분할** | `langchain_text_splitter.py` | ❌ (없음) | RecursiveCharacterTextSplitter vs 단순 결합 |

## 설치 및 실행

### 1. 환경 설정
```bash
# 필요한 패키지 설치
pip install -r requirements.txt

# PostgreSQL에서 pgvector 확장 설치
psql -d your_database -c "CREATE EXTENSION vector;"
```

### 2. 설정 파일 수정
`config.py`에서 다음 설정을 확인하세요:
```python
# OpenAI API 키
OPENAI_API_KEY = "your-openai-api-key"

# PostgreSQL 연결 정보
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "vectordb"
DB_USER = "postgres"
DB_PASSWORD = "password"
```

### 3. 서버 실행
```bash
# 실행 스크립트 사용
./run_langchain_server.sh

# 또는 직접 실행
uvicorn langchain_app:app --host 0.0.0.0 --port 8000 --reload
```

서버가 실행되면 다음 주소에서 확인할 수 있습니다:
- API 서버: http://localhost:8000
- API 문서: http://localhost:8000/docs

## API 사용법

### 1. 문서 추가
```bash
curl -X POST "http://localhost:8000/documents/" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "LangChain은 LLM 애플리케이션 개발을 위한 프레임워크입니다.",
    "metadata": {"source": "documentation"},
    "use_splitter": false
  }'
```

### 2. 시멘틱 서치
```bash
curl -X POST "http://localhost:8000/search/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "LLM 프레임워크",
    "limit": 3
  }'
```

### 3. RAG 질의응답
```bash
curl -X POST "http://localhost:8000/rag/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "LangChain이 무엇인가요?",
    "limit": 3
  }'
```

### 4. 뉴스 데이터 가져오기
```bash
curl -X POST "http://localhost:8000/import-news/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "인공지능",
    "limit": 10,
    "use_splitter": false
  }'
```