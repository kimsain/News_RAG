#!/bin/bash

# 프로젝트 실행 및 테스트 스크립트
# 이 스크립트는 필요한 패키지를 설치하고 프로젝트를 실행합니다.

echo "===== 프로젝트 실행 및 테스트 스크립트 ====="

# 현재 디렉토리 확인
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"
echo "작업 디렉토리: $(pwd)"

# 필요한 패키지 설치
echo "필요한 패키지를 설치합니다..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "패키지 설치 실패."
    exit 1
fi

# 데이터베이스 설정 스크립트 실행 권한 부여
chmod +x setup_db.sh

# 데이터베이스 설정 스크립트 실행
echo "데이터베이스 설정 스크립트를 실행합니다..."
./setup_db.sh

if [ $? -ne 0 ]; then
    echo "데이터베이스 설정 실패."
    exit 1
fi

# 실행 스크립트 권한 부여
chmod +x run_server.sh

# 샘플 데이터 생성 및 저장
echo "샘플 뉴스 데이터를 생성하고 JSON 파일로 저장합니다..."
python3 -c "
from sample_data import SampleNewsData
news_data = SampleNewsData()
news_data.save_to_json('sample_news_data.json')
print(f'샘플 뉴스 데이터 {len(news_data.news_data)}개가 저장되었습니다.')
"

if [ $? -ne 0 ]; then
    echo "샘플 데이터 생성 실패."
    exit 1
fi

# 테스트 실행
echo "단위 테스트를 실행합니다..."
python3 -c "
import unittest
from vector_db_manager import VectorDBManager
from bigkinds_api import BigkindsAPI
from config import APIConfig

class TestVectorDB(unittest.TestCase):
    def test_config(self):
        self.assertIsNotNone(APIConfig.OPENAI_API_KEY)
        self.assertTrue(APIConfig.USE_SAMPLE_DATA)
        
    def test_bigkinds_api(self):
        api = BigkindsAPI()
        results = api.search_news('저출산', 3)
        self.assertGreater(len(results), 0)
        self.assertIn('title', results[0])
        self.assertIn('content', results[0])
        
        categories = api.get_all_categories()
        self.assertGreater(len(categories), 0)
        
    def test_vector_db_connection(self):
        db = VectorDBManager()
        self.assertTrue(db.connect())
        db.disconnect()

if __name__ == '__main__':
    unittest.main()
"

if [ $? -ne 0 ]; then
    echo "테스트 실패."
    exit 1
fi

echo "===== 테스트 완료 ====="
echo "프로젝트를 실행하려면 다음 명령어를 사용하세요:"
echo "  ./run_server.sh"
echo ""
echo "또는 직접 실행:"
echo "  python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "웹 브라우저에서 다음 URL로 접속하세요:"
echo "  http://localhost:8000"
echo ""
echo "API 문서는 다음 URL에서 확인할 수 있습니다:"
echo "  http://localhost:8000/docs"
