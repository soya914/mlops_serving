# 1. 베이스 이미지 설정 (가벼운 파이썬 버전)
FROM python:3.13-slim

# 2. 작업 디렉토리 설정
WORKDIR /root/mlops_serving

# 3. 필수 라이브러리 설치
#    학습에 쓴 scikit-learn 버전(1.9.0)과 맞춰야 joblib 로드 경고/오류가 없습니다.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 모델 파일과 API 코드를 컨테이너 안으로 복사
COPY main.py .
COPY model.joblib .
# /model-info 가 읽는다. 없어도 서비스는 뜨지만 있으면 어떤 모델인지 확인할 수 있다.
COPY metrics.json .

# 5. 서버 실행 명령 (8000 포트)
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
