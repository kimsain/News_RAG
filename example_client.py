import os
import requests
import json
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# API 기본 URL
BASE_URL = "http://localhost:8000"

def add_document(content, metadata=None):
    """
    문서를 벡터 데이터베이스에 추가합니다.
    
    Args:
        content (str): 문서 내용
        metadata (dict): 문서 메타데이터
        
    Returns:
        dict: 추가된 문서 정보
    """
    url = f"{BASE_URL}/documents/"
    payload = {"content": content}
    if metadata:
        payload["metadata"] = metadata
    
    response = requests.post(url, json=payload)
    if response.status_code == 201:
        return response.json()
    else:
        print(f"문서 추가 실패: {response.status_code} - {response.text}")
        return None

def search_documents(query, limit=5):
    """
    쿼리와 유사한 문서를 검색합니다.
    
    Args:
        query (str): 검색 쿼리
        limit (int): 반환할 최대 문서 수
        
    Returns:
        list: 유사한 문서 목록
    """
    url = f"{BASE_URL}/search/"
    payload = {"query": query, "limit": limit}
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"문서 검색 실패: {response.status_code} - {response.text}")
        return []

def rag_query(query, limit=5):
    """
    RAG(Retrieval-Augmented Generation)를 사용하여 질의에 답변합니다.
    
    Args:
        query (str): 질의 내용
        limit (int): 검색할 문서 수
        
    Returns:
        dict: 답변 및 참조 문서
    """
    url = f"{BASE_URL}/rag/"
    payload = {"query": query, "limit": limit}
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"RAG 질의 실패: {response.status_code} - {response.text}")
        return None

def get_document(doc_id):
    """
    문서 ID로 문서를 조회합니다.
    
    Args:
        doc_id (int): 문서 ID
        
    Returns:
        dict: 문서 정보
    """
    url = f"{BASE_URL}/documents/{doc_id}"
    
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"문서 조회 실패: {response.status_code} - {response.text}")
        return None

def delete_document(doc_id):
    """
    문서 ID로 문서를 삭제합니다.
    
    Args:
        doc_id (int): 문서 ID
        
    Returns:
        bool: 삭제 성공 여부
    """
    url = f"{BASE_URL}/documents/{doc_id}"
    
    response = requests.delete(url)
    if response.status_code == 204:
        return True
    else:
        print(f"문서 삭제 실패: {response.status_code} - {response.text}")
        return False

def main():
    """
    예제 애플리케이션 실행
    """
    print("=== 벡터 데이터베이스 예제 애플리케이션 ===")
    
    # 샘플 문서 추가
    documents = [
        {
            "content": "인구 고령화는 한국 사회의 주요 문제 중 하나입니다. 2024년 기준 65세 이상 인구 비율이 20%를 넘어 초고령 사회로 진입했습니다.",
            "metadata": {"category": "인구통계", "source": "통계청", "year": 2024}
        },
        {
            "content": "한국의 출산율은 지속적으로 감소하고 있으며, 2023년 합계출산율은 0.72명으로 역대 최저치를 기록했습니다.",
            "metadata": {"category": "인구통계", "source": "통계청", "year": 2023}
        },
        {
            "content": "정부는 저출산 고령화 대책으로 다양한 정책을 시행하고 있으며, 육아 지원 및 노인 복지 정책에 예산을 확대하고 있습니다.",
            "metadata": {"category": "정책", "source": "보건복지부", "year": 2024}
        },
        {
            "content": "인구 구조 변화에 따라 노동 시장에도 변화가 필요하며, 고령자 고용 확대와 외국인 노동자 유입 정책이 논의되고 있습니다.",
            "metadata": {"category": "노동시장", "source": "고용노동부", "year": 2024}
        },
        {
            "content": "인구 감소는 지방 소멸 문제와도 연결되어 있으며, 특히 농촌 지역의 인구 감소가 심각한 상황입니다.",
            "metadata": {"category": "지역", "source": "행정안전부", "year": 2024}
        }
    ]
    
    print("\n1. 샘플 문서 추가 중...")
    doc_ids = []
    for doc in documents:
        result = add_document(doc["content"], doc["metadata"])
        if result:
            doc_ids.append(result["id"])
            print(f"  - 문서 추가 성공: ID {result['id']}")
    
    print(f"\n총 {len(doc_ids)}개 문서가 추가되었습니다.")
    
    # 벡터 검색 예제
    print("\n2. 벡터 검색 예제:")
    search_query = "한국의 출산율 현황"
    print(f"  검색 쿼리: '{search_query}'")
    
    search_results = search_documents(search_query)
    if search_results:
        print(f"  검색 결과 ({len(search_results)}개):")
        for i, result in enumerate(search_results):
            print(f"    {i+1}. [유사도: {result['similarity']:.4f}] {result['content'][:100]}...")
    
    # RAG 질의 예제
    print("\n3. RAG 질의 예제:")
    rag_query_text = "한국의 인구 문제와 정부 대책은 무엇인가요?"
    print(f"  질의: '{rag_query_text}'")
    
    rag_result = rag_query(rag_query_text)
    if rag_result:
        print("\n  답변:")
        print(f"    {rag_result['answer']}")
        print("\n  참조 문서:")
        for i, source in enumerate(rag_result['sources']):
            print(f"    {i+1}. [유사도: {source['similarity']:.4f}] {source['content'][:100]}...")
    
    # 문서 삭제 예제
    if doc_ids:
        print("\n4. 문서 삭제 예제:")
        doc_to_delete = doc_ids[0]
        print(f"  삭제할 문서 ID: {doc_to_delete}")
        
        success = delete_document(doc_to_delete)
        if success:
            print(f"  문서 ID {doc_to_delete} 삭제 성공")
        
        # 남은 문서 확인
        print("\n  남은 문서 확인:")
        for doc_id in doc_ids[1:]:
            doc = get_document(doc_id)
            if doc:
                print(f"    - ID {doc['id']}: {doc['content'][:100]}...")

if __name__ == "__main__":
    main()