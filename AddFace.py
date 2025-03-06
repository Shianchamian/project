from kivymd.app import MDApp
import cv2
import numpy as np
import os
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from insightface.app import FaceAnalysis  # ✅ Use ArcFace
from ManageFace import save_face_data

# # Initialize ArcFace model
# face_model = FaceAnalysis(name='buffalo_s')
# face_model.prepare(ctx_id=-1)

# Constants
CAPTURE_LIMIT = 20  # Number of face images to capture


class AddFaceScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.face_model = MDApp.get_running_app().face_model

        self.capture = None  # Camera instance
        self.clock_event = None  # Clock event
        self.captured_features = []  # List of face embeddings
        self.captured_images = []  # List of face images
        self.capture_count = 0  # Track number of captures

        # User input fields
        self.name_input = MDTextField(hint_text="Enter Name", multiline=False)
        self.relation_input = MDTextField(hint_text="Enter Relation", multiline=False)

        # UI Components
        self.layout = BoxLayout(orientation="vertical")
        self.info_label = MDLabel(text="Enter details and start capture.", halign="center")
        self.image = Image(allow_stretch=True, keep_ratio=True)
        self.capture_button = MDRaisedButton(text="Start Capture", on_release=self.start_capture, disabled=True)

        # Add components to layout
        self.layout.add_widget(self.name_input)
        self.layout.add_widget(self.relation_input)
        self.layout.add_widget(self.image)
        self.layout.add_widget(self.info_label)
        self.layout.add_widget(self.capture_button)
        self.add_widget(self.layout)

        # 降低更新频率
        self.frame_interval = 1.0/15  # 降至15fps
        # 添加状态标志
        self.is_capturing = False

    def on_enter(self, *args):
        """ Start camera when entering the screen """
        if not self.capture or not self.capture.isOpened():
            self.start_camera()

    def on_leave(self, *args):
        """ Ensure camera is released when leaving the screen """
        self.stop_camera()
        # print("Camera released from AddFaceScreen")

    def start_camera(self):
        """ Open camera and start face detection """
        self.capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.capture.set(cv2.CAP_PROP_FPS, 15)  # 限制摄像头帧率

        if not self.capture.isOpened():
            self.info_label.text = "Error: Unable to access camera"
            return

        self.clock_event = Clock.schedule_interval(self.update_frame, self.frame_interval)

    def stop_camera(self):
        """ Properly release the camera """
        if self.capture:
            self.capture.release()
            self.capture = None
        if self.clock_event:
            self.clock_event.cancel()

    def update_frame(self, dt):
        """ Detect faces and enable capture button """
        ret, frame = self.capture.read()
        if not ret:
            return
            
        # 降低处理分辨率
        frame = cv2.resize(frame, (320, 240))
        
        # 只在非捕捉状态检测人脸
        if not self.is_capturing:
            faces = self.face_model.get(frame)
            if faces:
                self.capture_button.disabled = False
                self.info_label.text = "Face detected! Press 'Start Capture' to begin"
            else:
                self.capture_button.disabled = True
                self.info_label.text = "No face detected"

        # 转换并显示图像
        display_frame = cv2.resize(frame, (640, 480))  # 显示时放大
        buf = cv2.flip(display_frame, 0).tobytes()
        texture = Texture.create(size=(display_frame.shape[1], display_frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.image.texture = texture

    def start_capture(self, instance):
        """ Start the capture process """
        if not self.name_input.text.strip() or not self.relation_input.text.strip():
            self.info_label.text = "Please enter name and relation first"
            return
            
        self.is_capturing = True
        self.capture_button.disabled = True
        self.captured_features = []
        self.captured_images = []
        self.capture_count = 0
        self.info_label.text = "Starting capture process..."
        Clock.schedule_interval(self.capture_face, 0.1)

    def capture_face(self, dt):
        """ Capture faces and extract features """
        if self.capture_count >= CAPTURE_LIMIT:
            self.is_capturing = False
            Clock.unschedule(self.capture_face)
            self.process_captured_faces()
            return False

        ret, frame = self.capture.read()
        if not ret:
            return False

        faces = self.face_model.get(frame)
        if faces:
            face = faces[0]
            embedding = face.normed_embedding
            self.captured_features.append(embedding)
            self.captured_images.append(frame)
            self.capture_count += 1
            self.info_label.text = f"Capturing... {self.capture_count}/{CAPTURE_LIMIT}"
            
        return True

    def process_captured_faces(self):
        """ Process and save captured faces """
        if not self.captured_features:
            self.info_label.text = "No faces captured. Try again."
            self.capture_button.disabled = False
            return

        self.info_label.text = "Processing captured faces..."
        
        # 计算平均特征
        avg_features = np.mean(self.captured_features, axis=0).astype(np.float32)
        
        # 选择最清晰的图片
        best_index = self.select_best_image(self.captured_images)
        best_image = self.captured_images[best_index]
        image_path = self.save_face_image(best_image, self.name_input.text.strip())

        # 保存到数据库
        name = self.name_input.text.strip()
        relation = self.relation_input.text.strip()
        save_face_data(name, relation, image_path, avg_features)

        # 重置UI
        self.info_label.text = "Face saved successfully!"
        self.name_input.text = ""
        self.relation_input.text = ""
        self.capture_button.disabled = False
        
        # 延迟2秒后重置提示文字
        Clock.schedule_once(lambda dt: setattr(self.info_label, 'text', 
                          "Enter details and start capture."), 2)

    def select_best_image(self, images):
        """ Select sharpest image based on Laplacian variance """
        def sharpness(image):
            return cv2.Laplacian(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()

        scores = [sharpness(img) for img in images]
        return np.argmax(scores)

    def save_face_image(self, image, name):
        # 确保两个目录都存在
        if not os.path.exists("saved_faces"):
            os.makedirs("saved_faces")
        if not os.path.exists("assets"):
            os.makedirs("assets")

        # 获取已存在的文件数量作为新的序号
        existing_files = len(os.listdir("saved_faces"))
        new_id = existing_files + 1
        
        # 保存到两个位置
        save_path = f"saved_faces/face_{new_id}.png"
        asset_path = f"assets/face_{new_id}.png"
        
        # 检测和裁剪人脸
        faces = self.face_model.get(image)
        if faces:
            face = faces[0]
            bbox = face.bbox.astype(int)
            x1, y1, x2, y2 = bbox
            
            # 扩大裁剪区域（20%边距）
            h, w = y2 - y1, x2 - x1
            margin_h = int(h * 0.2)
            margin_w = int(w * 0.2)
            
            # 确保边界不超出图像范围
            y1 = max(0, y1 - margin_h)
            y2 = min(image.shape[0], y2 + margin_h)
            x1 = max(0, x1 - margin_w)
            x2 = min(image.shape[1], x2 + margin_w)
            
            # 裁剪并调整大小
            face_image = image[y1:y2, x1:x2]
            face_image = cv2.resize(face_image, (256, 256))
        else:
            face_image = image  # 如果没检测到人脸，使用原图
        
        # 保存裁剪后的图片
        cv2.imwrite(save_path, face_image)  # 保存到saved_faces
        cv2.imwrite(asset_path, face_image)  # 保存到assets
        
        return asset_path  # 返回assets路径用于显示
