"""
PostgreSQL과 pgvector를 활용한 벡터 데이터베이스 관리 클래스

이 모듈은 PostgreSQL과 pgvector를 활용하여 벡터 데이터베이스를 관리하는 기능을 제공합니다.
중앙화된 API 키 관리 시스템을 활용합니다.
"""

import psycopg2
from psycopg2.extras import Json
from embedding_utils import generate_embedding
from config import APIConfig

class VectorDBManager:
    """
    PostgreSQL과 pgvector를 활용한 벡터 데이터베이스 관리 클래스
    """
    
    def __init__(self, dbname=None, user=None, password=None, host=None, port=None):
        """
        데이터베이스 연결 초기화
        """
        # 중앙화된 설정에서 DB 연결 정보 가져오기
        db_params = APIConfig.get_db_connection_params()
        
        self.conn_params = {
            "dbname": dbname or db_params["dbname"],
            "user": user or db_params["user"],
            "password": password or db_params["password"],
            "host": host or db_params["host"],
            "port": port or db_params["port"]
        }
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """
        데이터베이스에 연결
        """
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            print(f"데이터베이스 연결 오류: {e}")
            return False
            
    def disconnect(self):
        """
        데이터베이스 연결 종료
        """
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            
    def add_document(self, content, metadata=None):
        """
        문서를 데이터베이스에 추가하고 임베딩 생성
        
        Args:
            content (str): 문서 내용
            metadata (dict): 문서 메타데이터
            
        Returns:
            int: 추가된 문서의 ID
        """
        if not self.conn:
            if not self.connect():
                return None
                
        try:
            # 임베딩 생성
            embedding = generate_embedding(content)
            if not embedding:
                return None
                
            # 임베딩 배열을 PostgreSQL 배열 문법으로 변환
            embedding_str = str(embedding).replace('[', '{').replace(']', '}')
                
            # 문서 및 임베딩 저장
            self.cursor.execute(
                "INSERT INTO documents (content, metadata, embedding) VALUES (%s, %s, %s::vector) RETURNING id",
                (content, Json(metadata) if metadata else None, embedding_str)
            )
            doc_id = self.cursor.fetchone()[0]
            self.conn.commit()
            return doc_id
        except Exception as e:
            self.conn.rollback()
            print(f"문서 추가 오류: {e}")
            return None
            
    def search_similar_documents(self, query_text, limit=5):
        """
        쿼리 텍스트와 유사한 문서 검색
        
        Args:
            query_text (str): 검색 쿼리 텍스트
            limit (int): 반환할 최대 문서 수
            
        Returns:
            list: 유사한 문서 목록 (id, content, metadata, similarity)
        """
        if not self.conn:
            if not self.connect():
                return []
                
        try:
            # 쿼리 텍스트의 임베딩 생성
            query_embedding = generate_embedding(query_text)
            if not query_embedding:
                return []
                
            # 벡터 유사도 검색 수행 - 명시적 타입 변환 추가
            query_embedding_str = str(query_embedding).replace('[', '{').replace(']', '}')
            
            self.cursor.execute(
                """
                SELECT id, content, metadata, 1 - (embedding <-> %s::vector) AS similarity
                FROM documents
                ORDER BY embedding <-> %s::vector
                LIMIT %s
                """,
                (query_embedding_str, query_embedding_str, limit)
            )
            
            results = []
            for row in self.cursor.fetchall():
                results.append({
                    "id": row[0],
                    "content": row[1],
                    "metadata": row[2],
                    "similarity": row[3]
                })
            
            return results
        except Exception as e:
            print(f"유사 문서 검색 오류: {e}")
            return []
            
    def delete_document(self, doc_id):
        """
        문서 ID로 문서 삭제
        
        Args:
            doc_id (int): 삭제할 문서 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        if not self.conn:
            if not self.connect():
                return False
                
        try:
            self.cursor.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"문서 삭제 오류: {e}")
            return False
            
    def get_document(self, doc_id):
        """
        문서 ID로 문서 조회
        
        Args:
            doc_id (int): 조회할 문서 ID
            
        Returns:
            dict: 문서 정보
        """
        if not self.conn:
            if not self.connect():
                return None
                
        try:
            self.cursor.execute("SELECT id, content, metadata FROM documents WHERE id = %s", (doc_id,))
            row = self.cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "content": row[1],
                    "metadata": row[2]
                }
            return None
        except Exception as e:
            print(f"문서 조회 오류: {e}")
            return None
            
    def import_news_data(self, news_api, query=None, category=None, limit=10):
        """
        뉴스 API에서 데이터를 가져와 벡터 데이터베이스에 저장
        
        Args:
            news_api: 뉴스 API 인스턴스
            query (str): 검색 쿼리 (선택적)
            category (str): 뉴스 카테고리 (선택적)
            limit (int): 가져올 뉴스 수
            
        Returns:
            list: 추가된 문서 ID 목록
        """
        if not self.conn:
            if not self.connect():
                return []
                
        try:
            news_data = []
            
            # 쿼리로 검색
            if query:
                news_data = news_api.search_news(query, limit)
            # 카테고리로 검색
            elif category:
                news_data = news_api.get_news_by_category(category, limit)
            # 최신 뉴스 가져오기
            else:
                news_data = news_api.get_recent_news(limit)
                
            # 뉴스 데이터를 벡터 데이터베이스에 저장
            doc_ids = []
            for news in news_data:
                # 뉴스 내용 구성
                content = f"{news['title']}\n\n{news['content']}"
                
                # 메타데이터 구성
                metadata = {
                    "source": news.get("source", ""),
                    "date": news.get("date", ""),
                    "category": news.get("category", ""),
                    "keywords": news.get("keywords", []),
                    "news_id": news.get("id", "")
                }
                
                # 임베딩 생성
                embedding = generate_embedding(content)
                if not embedding:
                    continue
                    
                # 임베딩 배열을 PostgreSQL 배열 문법으로 변환
                embedding_str = str(embedding).replace('[', '{').replace(']', '}')
                    
                # 문서 및 임베딩 저장
                self.cursor.execute(
                    "INSERT INTO documents (content, metadata, embedding) VALUES (%s, %s, %s::vector) RETURNING id",
                    (content, Json(metadata) if metadata else None, embedding_str)
                )
                doc_id = self.cursor.fetchone()[0]
                self.conn.commit()
                doc_ids.append(doc_id)
                    
            return doc_ids
        except Exception as e:
            self.conn.rollback()
            print(f"뉴스 데이터 가져오기 오류: {e}")
            return []
