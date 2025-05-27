"""
임베딩 유틸리티 모듈

이 모듈은 OpenAI API를 사용하여 텍스트의 임베딩 벡터를 생성하는 기능을 제공합니다.
중앙화된 API 키 관리 시스템을 활용합니다.
"""

import openai
from config import APIConfig

# OpenAI API 키 설정
openai.api_key = APIConfig.OPENAI_API_KEY

def generate_embedding(text):
    """
    OpenAI API를 사용하여 텍스트의 임베딩 벡터를 생성합니다.
    
    Args:
        text (str): 임베딩할 텍스트
        
    Returns:
        list: 임베딩 벡터
    """
    try:
        # OpenAI의 임베딩 모델 사용
        response = openai.Embedding.create(
            model=APIConfig.OPENAI_EMBEDDING_MODEL,
            input=text
        )
        # 임베딩 벡터 반환
        return response['data'][0]['embedding']
    except Exception as e:
        print(f"임베딩 생성 중 오류 발생: {e}")
        return None
