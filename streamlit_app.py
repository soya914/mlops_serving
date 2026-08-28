import os

import streamlit as st
import requests

# 백엔드 주소. 컨테이너로 띄울 땐 API_URL 환경변수로 덮어쓴다.
# 같은 VM 안의 다른 컨테이너에서 부를 땐 http://172.17.0.1/predict (도커 브리지 게이트웨이)
API_URL = os.getenv("API_URL", "http://34.10.33.109/predict")

st.title("붓꽃 분류기 (Iris Classifier)")

s_l = st.slider("꽃받침 길이", 0.0, 8.0, 5.0)
s_w = st.slider("꽃받침 너비", 0.0, 4.5, 3.0)
p_l = st.slider("꽃잎 길이", 0.0, 7.0, 1.5)
p_w = st.slider("꽃잎 너비", 0.0, 2.5, 0.2)

if st.button("예측하기"):
    try:
        res = requests.post(API_URL, json={"data": [s_l, s_w, p_l, p_w]}, timeout=5)
        st.success(f"예측된 클래스 번호: {res.json()['class_index']}")
    except requests.exceptions.RequestException:
        st.error("API 서버에 연결할 수 없어요. VM이 켜져 있는지, IP가 맞는지 확인!")
