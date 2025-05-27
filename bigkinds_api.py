"""
빅카인드 API 연동 모듈

이 모듈은 빅카인드 API를 사용하여 뉴스 데이터를 수집하는 기능을 제공합니다.
현재 API 키 발급이 중지된 상태이므로, 샘플 데이터를 사용하도록 구현되어 있습니다.
실제 API 키가 발급되면 이 모듈을 수정하여 실제 API를 사용할 수 있습니다.
"""

import requests
import json
from typing import List, Dict, Any, Optional
from config import APIConfig
from sample_data import SampleNewsData

class BigkindsAPI:
    """빅카인드 API 연동 클래스"""
    
    def __init__(self):
        """API 초기화"""
        self.api_key = APIConfig.BIGKINDS_API_KEY
        self.api_url = APIConfig.BIGKINDS_API_URL
        self.use_sample_data = APIConfig.USE_SAMPLE_DATA
        
        # 샘플 데이터 인스턴스 생성
        if self.use_sample_data:
            self.sample_data = SampleNewsData()
    
    def search_news(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        뉴스 검색 API
        
        Args:
            query (str): 검색 쿼리
            limit (int): 반환할 최대 결과 수
            
        Returns:
            List[Dict[str, Any]]: 검색 결과 목록
        """
        # 샘플 데이터 사용 모드
        if self.use_sample_data or not self.api_key:
            return self.sample_data.search_news(query, limit)
        
        # 실제 API 사용 모드 (API 키가 발급되면 아래 코드 활성화)
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "query": query,
                "limit": limit
            }
            
            response = requests.post(
                f"{self.api_url}/search",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                return response.json().get("data", [])
            else:
                print(f"API 요청 실패: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"API 요청 중 오류 발생: {e}")
            return []
    
    def get_news_by_id(self, news_id: int) -> Optional[Dict[str, Any]]:
        """
        뉴스 ID로 상세 정보 조회
        
        Args:
            news_id (int): 뉴스 ID
            
        Returns:
            Optional[Dict[str, Any]]: 뉴스 상세 정보
        """
        # 샘플 데이터 사용 모드
        if self.use_sample_data or not self.api_key:
            return self.sample_data.get_news_by_id(news_id)
        
        # 실제 API 사용 모드 (API 키가 발급되면 아래 코드 활성화)
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.api_url}/news/{news_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json().get("data")
            else:
                print(f"API 요청 실패: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"API 요청 중 오류 발생: {e}")
            return None
    
    def get_recent_news(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        최신 뉴스 조회
        
        Args:
            limit (int): 반환할 최대 결과 수
            
        Returns:
            List[Dict[str, Any]]: 최신 뉴스 목록
        """
        # 샘플 데이터 사용 모드
        if self.use_sample_data or not self.api_key:
            return self.sample_data.get_recent_news(limit)
        
        # 실제 API 사용 모드 (API 키가 발급되면 아래 코드 활성화)
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.api_url}/news/recent?limit={limit}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json().get("data", [])
            else:
                print(f"API 요청 실패: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"API 요청 중 오류 발생: {e}")
            return []
    
    def get_news_by_category(self, category: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        카테고리별 뉴스 조회
        
        Args:
            category (str): 뉴스 카테고리
            limit (int): 반환할 최대 결과 수
            
        Returns:
            List[Dict[str, Any]]: 카테고리별 뉴스 목록
        """
        # 샘플 데이터 사용 모드
        if self.use_sample_data or not self.api_key:
            return self.sample_data.get_news_by_category(category, limit)
        
        # 실제 API 사용 모드 (API 키가 발급되면 아래 코드 활성화)
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.api_url}/news/category/{category}?limit={limit}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json().get("data", [])
            else:
                print(f"API 요청 실패: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"API 요청 중 오류 발생: {e}")
            return []
    
    def get_all_categories(self) -> List[str]:
        """
        모든 뉴스 카테고리 목록 조회
        
        Returns:
            List[str]: 카테고리 목록
        """
        # 샘플 데이터 사용 모드
        if self.use_sample_data or not self.api_key:
            return self.sample_data.get_all_categories()
        
        # 실제 API 사용 모드 (API 키가 발급되면 아래 코드 활성화)
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.api_url}/categories",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json().get("data", [])
            else:
                print(f"API 요청 실패: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"API 요청 중 오류 발생: {e}")
            return []
