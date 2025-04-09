import tkinter as tk
from tkinter import ttk, messagebox
import pyaudio
import wave
import openai
import pyautogui
import keyboard
import threading
import os
import numpy as np
from datetime import datetime
import time

class VoiceInApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VoiceIn")
        self.root.geometry("300x150")
        
        # OpenAI API 키 설정
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        # 녹음 관련 변수
        self.recording = False
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.last_sound_time = 0
        self.silence_threshold = 0.01  # 소리 감지 임계값
        self.silence_duration = 2  # 무음 지속 시간 (초)
        
        # UI 생성
        self.create_widgets()
        
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
        
    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()
            
    def start_recording(self):
        self.recording = True
        self.record_button.config(text="중지")
        self.status_label.config(text="녹음 중...")
        self.last_sound_time = time.time()
        
        # 녹음 시작
        self.frames = []
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            frames_per_buffer=1024,
            stream_callback=self.audio_callback
        )
        
        # 무음 감지 스레드 시작
        threading.Thread(target=self.check_silence, daemon=True).start()
        
    def stop_recording(self):
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
            if np.abs(audio_data).mean() > self.silence_threshold:
                self.last_sound_time = time.time()
        return (in_data, pyaudio.paContinue)
        
    def check_silence(self):
        while self.recording:
            if time.time() - self.last_sound_time > self.silence_duration:
                # 무음 감지 시 사용자에게 확인
                self.root.after(0, self.ask_for_conversion)
                break
            time.sleep(0.1)
            
    def ask_for_conversion(self):
        if not self.recording:
            return
            
        self.recording = False
        self.record_button.config(text="시작")
        self.status_label.config(text="대기 중...")
        
        # 녹음 중지
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            
        # 오디오 파일 저장
        filename = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        self.save_audio(filename)
        
        # 사용자 확인
        response = messagebox.askquestion(
            "텍스트 변환",
            "텍스트로 변환하시겠습니까?",
            icon='question'
        )
        
        if response == 'yes':
            self.status_label.config(text="처리 중...")
            threading.Thread(target=self.process_audio, args=(filename,)).start()
        else:
            os.remove(filename)
            self.status_label.config(text="대기 중...")
        
    def save_audio(self, filename):
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        
    def process_audio(self, filename):
        try:
            # 오디오 파일을 텍스트로 변환
            with open(filename, "rb") as audio_file:
                transcript = openai.Audio.transcribe(
                    "whisper-1",
                    audio_file
                )
                
            # 변환된 텍스트를 마우스 커서 위치에 입력
            pyautogui.write(transcript.text)
            
            # 임시 파일 삭제
            os.remove(filename)
            
            self.status_label.config(text="완료!")
        except Exception as e:
            self.status_label.config(text=f"오류: {str(e)}")
            
    def on_closing(self):
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