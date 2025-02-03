import logging

from fastapi import FastAPI             # 파이썬 웹 개발 api
from pydantic import BaseModel    # 유효성 검사
from starlette.middleware.base import BaseHTTPMiddleware
# 요청(req)과 응답(res) 사이에 특정 작업 수행
# 미들웨어는 모든 요청에 대해 실행되며, 요청을 처리하기 전에 응답을 변환하기 전에 특정 작업을 수행할 수 있음
# 예를 들어 로깅, 인증, cors처리 압축 등..

app = FastAPI(
    title="MBC AI 프로젝트 Test",
    description="파이썬과 자바부트를 연동한 ai앱",
    version="1.0.0",
    # docs_url=None, http://127.0.0.1:8001/docs 보안상 None처리함
    # redoc_url=None http://127.0.0.1:8001/redoc
)           # FastAPI() 객체 생성해서 app 변수에 넣음

class LoggingMiddleware(BaseHTTPMiddleware): # 로그를 콘솔에 출력하는 용도
  logging.basicConfig(level=logging.INFO)
  async def dispatch(self, request, call_next):
    logging.info(f"req : {request.method} {request.url} is called")
    response = await call_next(request)
    logging.info(f"status_code : {response.status_code}")
    return response

app.add_middleware(LoggingMiddleware)

class Item(BaseModel):      # 아이템 객체 생성 (BaseModel : 객체 연결 -> 상속)
  name: str                           # 상품명 : 문자열
  description: str = None    # 상품설명 : 문자열(Null)
  price: float                          # 가격 : 실수형
  tax: float = None               # 세금 : 실수형 (Null)

@app.post("/items/")     # post 메서드용 응답
async def create_item(item: Item):  # BaseModel 은 데이터 모델링을 쉽게 도와주고 유효성 검사도 수행함
  # 잘못된 데이터가 들어오면 422 오류코드를 반환
  return item

# 컨트롤러 검증은 postman으로 활용해 보았는데 내장된 백검증 툴도 있다.

@app.get("/")    # http://ip주소:포트/(루트컨텍스트)
async def read_root():
  return {"message": "Hello World"}

@app.get("/items/{item_id}")    # http://ip주소:포트/items/1
async def read_item(item_id: int, q: str = None):
  return {"item_id": item_id, "q": q}
  # item_id : 상품의 번호 -> 경로 매개변수
  # q : 쿼리 매개변수 (기본값 none)