# 선행 준비 : ip 카메라를 준비한다.
# ip 카메라의 제조회사에 가서 관련 네트워크 설정을 마무리 한다.
# 제조회사의 vms 프로그램을 설치한다. (ip와 암호, rtsp 활성화)

# 파이썬과 프론트를 연동하는 mqtt api를 활용한다.
# mqtt : 실시간 출력 프로토콜 https://underflow101.tistory.com/22
# mqtt 브로커용 프로그램 모스키토 api를 활용한다.
# https://mosquitto.org/download/ 꼭 버전 2.0.18 사용
# 모스키토 환경설정 변경 "C:\Program Files\mosquitto\mosquitto.conf"

import base64
import io
from PIL import Image
import numpy as np
import json
from ultralytics import YOLO
# 브로커 추가 (mosquitto 실행중)
import paho.mqtt.client as mqtt
import cv2
import time

model = YOLO('yolov8n.pt')
# mosquitto -c mosquitto.conf (여기에 더해서 -v 치면 화면에 상태뜸)
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
# 인텔리제이 터미널 (powershell) 에서 바로 켜기 -> & "C:\Program Files\mosquitto\mosquitto" -c "C:\Program Files\mosquitto\mosquitto.conf" -v
topic = '/camera/objects'

# mosquitto 브로커와 연결, 60초마다 핑으로 연결 확인
client.connect('localhost', 1883, 60)


# 연결용 함수
def on_connect(client, userdata, flags, rc):
  print(f"Connected with result code {rc}")

# 객체 감지용 사각박스 함수
def get_colors(num_colors):
  np.random.seed(0)
  colors = [tuple(np.random.randint(0, 255, 3).tolist()) for _ in range(num_colors)]
  return colors

class_names = model.names          # 모델에서 받은 클래스 이름
num_classes = len(class_names)   # 클래스 번호
colors = get_colors(num_classes)  # 사각박스 컬러색

client.on_connect = on_connect # 클라이언트 연결 정보

def detect_objects(image: np.array):
  results = model(image, verbose=False)
  class_names = model.names

  for result in results:
    boxes = result.boxes.xyxy
    confidences = result.boxes.conf
    class_ids = result.boxes.cls

    for box, confidence, class_id in zip(boxes, confidences, class_ids):
      x1, y1, x2, y2 = map(int, box)
      label = class_names[int(class_id)]
      cv2.rectangle(image, (x1, y1), (x2, y2), colors[int(class_id)], 2)
      cv2.putText(image, f'{label} {confidence:.2f}', (x1, y1),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.9, colors[int(class_id)], 2)
      return image


cap = cv2.VideoCapture('rtsp://admin:mbc312AI!!@192.168.0.8:554/taem1')

# https://deep-learning-study.tistory.com/107
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

while True:
  ret, frame = cap.read()
  if ret:
    # 프레임이 읽히면 탐지
    # resized_frame = cv2.resize(frame, (1600, 900), interpolation=cv2.INTER_AREA)
    # result_image = detect_objects(resized_frame)
    result_image = detect_objects(frame)
  else:
    continue

  if result_image is not None:
    success, buffer = cv2.imencode('.jpg', result_image)
    if success:
      jpg_as_text = base64.b64encode(buffer).decode('utf-8')
      payload = json.dumps({'image': jpg_as_text})
      client.publish(topic, payload)

    # 화면 표시
    #cv2.imshow('frame', result_image)

  if cv2.waitKey(1) & 0xFF == ord('q'):  # 영상 출력중에 q가 입력되면 종료
    break

# # 객체 탐지 반복용 루프
# while cap.isOpened():
#   ret, frame = cap.read()
#   if not ret:
#     break
#   result_image = detect_objects(frame)
#
#   _, buffer = cv2.imencode('.jpg', result_image)
#   jpg_as_text = base64.b64encode(buffer).decode('utf-8')
#
#   payload = json.dumps({'image': jpg_as_text})
#   client.publish(topic, payload)
#   cv2.imshow('frame', result_image)
#
#   if cv2.waitKey(1) & 0xFF == ord('q'): # 영상 출력중에 q가 입력되면 종료
#     break

cap.release()                       # VideoCapture
cv2.destroyAllWindows()   # 창 닫기
client.disconnect()               # 연결 해제