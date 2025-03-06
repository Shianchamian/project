from kivy.utils import platform
from threading import Thread
import time

class VoiceManager:
    def __init__(self):
        self.is_speaking = False
        self.tts = None
        
        # 根据平台初始化TTS
        if platform == 'android':
            from android.tts import TTS
            self.tts = TTS()
        else:
            # Windows或其他平台使用pyttsx3
            import pyttsx3
            self.tts = pyttsx3.init()
            self.tts.setProperty('rate', 150)
            self.tts.setProperty('volume', 0.9)
    
    def speak(self, text):
        """非阻塞的语音播报"""
        if not self.is_speaking:
            self.is_speaking = True
            Thread(target=self._speak_thread, args=(text,), daemon=True).start()
    
    def _speak_thread(self, text):
        """在独立线程中进行语音播报"""
        try:
            if platform == 'android':
                self.tts.speak(text)
            else:
                self.tts.say(text)
                self.tts.runAndWait()
        finally:
            self.is_speaking = False
            time.sleep(0.1)  # 防止连续播放时的冲突
    
    def verification_success(self, name, relation):
        """验证通过消息"""
        success_text = f"Welcome {name}! I recognize you as my {relation}."
        self.speak(success_text)
    
    def alert_message(self, message):
        """警告消息"""
        alert_text = "This face is not in your database. Please carefully verify their identity."
        self.speak(alert_text)
    
    def stop(self):
        """停止语音播报"""
        if platform == 'android':
            if self.tts:
                self.tts.stop()
        else:
            if self.tts:
                try:
                    self.tts.stop()
                except:
                    pass 
    
    def face_detected(self):
        """检测到人脸时的提示"""
        prompt_text = "Please click the button to start adding this person."
        self.speak(prompt_text) 

    def no_face_detected(self):
        """未检测到人脸时的提示"""
        prompt_text = "Face is not visible. Please adjust your position."
        self.speak(prompt_text)
