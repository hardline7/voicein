# VoiceIn

음성 입력을 텍스트로 변환하여 마우스 커서 위치에 입력하는 프로그램입니다.

## 기능

- 시작/중지 버튼으로 음성 입력 제어
- OpenAI Whisper API를 사용한 음성-텍스트 변환
- 마우스 커서 위치에 자동 텍스트 입력

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. OpenAI API 키 설정:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

## 사용 방법

1. 프로그램 실행:
```bash
python voicein.py
```

2. 시작 버튼을 클릭하여 음성 입력 시작
3. 말하기를 마치면 중지 버튼을 클릭
4. 변환된 텍스트가 마우스 커서 위치에 자동으로 입력됨

## 시스템 요구사항

- Python 3.7 이상
- 마이크
- OpenAI API 키 