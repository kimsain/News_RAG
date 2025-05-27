#!/bin/bash

# 데이터베이스 스키마 설정 스크립트
# 이 스크립트는 PostgreSQL 데이터베이스와 PGVector 확장을 설정하고 필요한 테이블을 생성합니다.

echo "===== PostgreSQL 및 PGVector 설정 스크립트 ====="

# PostgreSQL 서비스 상태 확인
if systemctl is-active --quiet postgresql; then
    echo "PostgreSQL 서비스가 실행 중입니다."
else
    echo "PostgreSQL 서비스를 시작합니다..."
    sudo service postgresql start
    
    if [ $? -ne 0 ]; then
        echo "PostgreSQL 서비스 시작 실패. PostgreSQL이 설치되어 있는지 확인하세요."
        echo "설치 방법: sudo apt-get update && sudo apt-get install -y postgresql postgresql-contrib"
        exit 1
    fi
fi

# PostgreSQL 버전 확인
PG_VERSION=$(psql --version | grep -oP 'psql \(PostgreSQL\) \K[0-9]+')
echo "PostgreSQL 버전: $PG_VERSION"

# 데이터베이스 존재 여부 확인
DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='vector_db'")

if [ "$DB_EXISTS" = "1" ]; then
    echo "vector_db 데이터베이스가 이미 존재합니다."
    
    # 기존 테이블 삭제 여부 확인
    read -p "기존 테이블을 삭제하고 새로 생성하시겠습니까? (y/n): " RESET_DB
    if [ "$RESET_DB" = "y" ]; then
        echo "documents 테이블을 삭제합니다..."
        sudo -u postgres psql -d vector_db -c "DROP TABLE IF EXISTS documents;"
    fi
else
    echo "vector_db 데이터베이스를 생성합니다..."
    sudo -u postgres psql -c "CREATE DATABASE vector_db;"
    
    if [ $? -ne 0 ]; then
        echo "데이터베이스 생성 실패."
        exit 1
    fi
fi

# PGVector 확장 활성화
echo "PGVector 확장을 활성화합니다..."
sudo -u postgres psql -d vector_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

if [ $? -ne 0 ]; then
    echo "PGVector 확장 활성화 실패. PGVector가 설치되어 있는지 확인하세요."
    echo "설치 방법:"
    echo "  sudo apt-get install -y git build-essential postgresql-server-dev-$PG_VERSION"
    echo "  git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git"
    echo "  cd pgvector"
    echo "  make"
    echo "  sudo make install"
    exit 1
fi

# 테이블 생성
echo "documents 테이블을 생성합니다..."
sudo -u postgres psql -d vector_db -c "
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding VECTOR(1536)
);"

if [ $? -ne 0 ]; then
    echo "테이블 생성 실패."
    exit 1
fi

# 인덱스 생성
echo "벡터 인덱스를 생성합니다..."
sudo -u postgres psql -d vector_db -c "
CREATE INDEX IF NOT EXISTS documents_embedding_idx 
ON documents USING ivfflat (embedding vector_l2_ops) 
WITH (lists = 100);"

if [ $? -ne 0 ]; then
    echo "인덱스 생성 실패."
    exit 1
fi

echo "===== 데이터베이스 설정 완료 ====="
echo "데이터베이스: vector_db"
echo "테이블: documents"
echo "인덱스: documents_embedding_idx (IVFFlat)"
