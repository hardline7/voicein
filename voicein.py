import tkinter as tk
from tkinter import ttk, messagebox
import pyaudio
import wave
from openai import OpenAI
import pyautogui
import keyboard
import threading
import os
import numpy as np
from datetime import datetime
import time
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class VoiceInApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VoiceIn")
        self.root.geometry("300x150")
        
        # 항상 최상단에 표시
        self.root.attributes('-topmost', True)
        
        # OpenAI 클라이언트 초기화
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # 녹음 관련 변수
        self.recording = False
        self.waiting_for_click = False
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.last_sound_time = 0
        self.silence_threshold = 500
        self.silence_duration = 2
        
        # 오디오 설정
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        
        # UI 생성
        self.create_widgets()
        
        # 마우스 클릭 이벤트 감지 스레드
        self.click_thread = None
        
    def create_widgets(self):
        # 시작/중지 버튼
        self.record_button = ttk.Button(
            self.root, 
            text="시작", 
            command=self.toggle_recording
        )
        self.record_button.pack(pady=20)
        
        # 상태 표시 레이블
        self.status_label = ttk.Label(
            self.root, 
            text="대기 중...",
            font=("Arial", 12)
        )
        self.status_label.pack(pady=10)
        
    def wait_for_click(self):
        self.waiting_for_click = True
        self.status_label.config(text="텍스트를 입력할 위치를 클릭해주세요...")
        
        def on_click(x, y, button, pressed):
            if pressed and self.waiting_for_click:
                self.waiting_for_click = False
                time.sleep(1)  # 1초 대기
                self.root.after(0, self.start_recording)
                return False  # 리스너 중지
        
        # 마우스 클릭 이벤트 감지
        from pynput import mouse
        self.click_thread = mouse.Listener(on_click=on_click)
        self.click_thread.start()
            
    def toggle_recording(self):
        if not self.recording and not self.waiting_for_click:
            self.wait_for_click()
        elif self.recording:
            self.stop_recording()
            
    def start_recording(self):
        self.recording = True
        self.record_button.config(text="중지")
        self.status_label.config(text="녹음 중...")
        self.last_sound_time = time.time()
        
        # 녹음 시작
        self.frames = []
        self.stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
            stream_callback=self.audio_callback
        )
        
        # 무음 감지 스레드 시작
        threading.Thread(target=self.check_silence, daemon=True).start()
        
    def stop_recording(self):
        if not self.recording:  # 이미 중지된 경우 무시
            return
            
        self.recording = False
        self.record_button.config(text="시작")
        self.status_label.config(text="처리 중...")
        
        # 녹음 중지
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            
        # 오디오 파일 저장
        filename = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        self.save_audio(filename)
        
        # 텍스트 변환 및 입력
        threading.Thread(target=self.process_audio, args=(filename,)).start()
        
    def audio_callback(self, in_data, frame_count, time_info, status):
        if self.recording:
            self.frames.append(in_data)
            # 소리 크기 계산
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            volume = np.abs(audio_data).mean()
            if volume > self.silence_threshold:
                self.last_sound_time = time.time()
        return (in_data, pyaudio.paContinue)
        
    def check_silence(self):
        while self.recording:
            current_time = time.time()
            if current_time - self.last_sound_time > self.silence_duration:
                # 무음 감지 시 녹음 중지
                self.root.after(0, self.stop_recording)
                break
            time.sleep(0.1)
            
    def save_audio(self, filename):
        try:
            print("오디오 저장 시작...")
            print(f"프레임 수: {len(self.frames)}")
            
            wf = wave.open(filename, 'wb')
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            
            audio_data = b''.join(self.frames)
            print(f"오디오 데이터 크기: {len(audio_data)} bytes")
            
            wf.writeframes(audio_data)
            wf.close()
            print("오디오 저장 완료")
            
        except Exception as e:
            print(f"오디오 저장 중 에러 발생: {str(e)}")
            raise e
        
    def process_audio(self, filename):
        try:
            print(f"녹음 파일 생성됨: {filename}")
            print(f"파일 크기: {os.path.getsize(filename)} bytes")
            
            # 오디오 파일을 텍스트로 변환
            with open(filename, "rb") as audio_file:
                print("Whisper API 호출 시작...")
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ko",
                    response_format="text",
                    temperature=0.0,
                    prompt="이것은 한국어 음성입니다. 한국어로 정확하게 받아써주세요."
                )
                print(f"Whisper 응답: {transcript}")
            
            # 디버깅을 위해 임시로 파일 보존
            debug_filename = f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            import shutil
            shutil.copy(filename, debug_filename)
            print(f"디버깅용 파일 저장됨: {debug_filename}")
            
            # keyboard 모듈을 사용하여 한글 텍스트 입력
            time.sleep(0.5)
            keyboard.write(transcript)
            
            # 원본 임시 파일 삭제
            os.remove(filename)
            
            self.status_label.config(text="완료!")
        except Exception as e:
            print(f"에러 발생: {str(e)}")
            self.status_label.config(text=f"오류: {str(e)}")
            
    def on_closing(self):
        self.waiting_for_click = False
        if self.click_thread and self.click_thread.is_alive():
            self.click_thread.stop()
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceInApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop() 