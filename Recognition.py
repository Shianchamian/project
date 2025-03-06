from kivymd.app import MDApp
import cv2
import numpy as np
import sqlite3
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivy.uix.boxlayout import BoxLayout
from insightface.app import FaceAnalysis
from ManageFace import manage_face  # Import database functions

# Initialize ArcFace (lightweight model for face recognition)
app = FaceAnalysis(name="buffalo_s")
app.prepare(ctx_id=-1)  # -1 means using CPU (set GPU index if available)

# Camera index (0 = front, 1 = back)
current_camera = 0


class RecognitionScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.face_model = MDApp.get_running_app().face_model
        self.capture = None  # Camera object
        self.clock_event = None  # Clock for updating frames

        # UI Components
        self.layout = BoxLayout(orientation="vertical")

        self.image = Image(allow_stretch=True, keep_ratio=True)  # Camera feed display
        self.username_label = MDLabel(text="Detecting...", halign="center", font_style="H6")
        self.confidence_label = MDLabel(text="", halign="center", theme_text_color="Secondary")
        self.switch_camera_button = MDRaisedButton(text="Switch Camera", on_release=self.switch_camera)

        # Add UI components
        self.layout.add_widget(self.image)
        self.layout.add_widget(self.username_label)
        self.layout.add_widget(self.confidence_label)
        self.layout.add_widget(self.switch_camera_button)
        self.add_widget(self.layout)

        # Load known faces from the database
        self.known_faces = self.load_known_faces()

    def load_known_faces(self):
        """Load stored face data from the database"""
        faces = manage_face()  # Fetch (id, name, relation, image_path)
        known_faces = {}
        for face in faces:
            face_id, name, _, _ = face  # Store only ID and Name
            known_faces[face_id] = name
        return known_faces  # Returns {id: name} dictionary

    def on_enter(self, *args):
        """Start camera when entering the screen"""
        self.start_capture()

    def start_capture(self):
        """Check if camera is already open before starting a new session."""
        self.capture = cv2.VideoCapture(current_camera)
        if not self.capture.isOpened():
            self.username_label.text = "Error: Unable to access camera"
            return

        Clock.schedule_interval(self.update_frame, 1.0 / 60)

    def update_frame(self, dt):
        """Process real-time face recognition"""
        ret, frame = self.capture.read()
        if not ret:
            return

        faces = app.get(frame)  # Detect faces using ArcFace

        detected_name = "Unknown"
        confidence_score = 0.0

        for face in faces:
            x, y, w, h = face.bbox.astype(int)  # Get face bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)  # Draw a rectangle around the face

            # Extract facial features
            new_face = face.normed_embedding

            # Compare with known faces
            detected_name, confidence_score = self.find_best_match(new_face)

            # Display recognition results
            cv2.putText(frame, f"{detected_name} ({confidence_score:.2f}%)", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

        # Update UI labels
        self.username_label.text = f"Detected: {detected_name}"
        self.confidence_label.text = f"Confidence: {confidence_score:.2f}%"

        # Convert OpenCV frame to Kivy-compatible texture
        buf = cv2.flip(frame, 0).tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.image.texture = texture  # Update UI with the latest frame

    def find_best_match(self, new_face):
        """Compare detected face with stored faces in the database"""
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, features FROM faces")
        known_faces = cursor.fetchall()
        conn.close()

        best_match = "Unknown"
        best_score = 0

        for face_id, name, stored_features in known_faces:
            stored_features = np.frombuffer(stored_features, dtype=np.float32)  # ✅ Ensure 512D
            if stored_features.shape[0] != 512:
                continue  # Skip invalid data

            score = np.dot(new_face, stored_features) / (np.linalg.norm(new_face) * np.linalg.norm(stored_features))

            if score > best_score:
                best_score = score
                best_match = name

        return best_match if best_score > 0.6 else "Unknown", best_score * 100

    def switch_camera(self, *args):
        """Switch between front and back cameras"""
        global current_camera
        current_camera = 1 - current_camera
        self.capture.release()
        self.start_capture()

    def on_leave(self, *args):
        """Release camera resources when leaving the screen"""
        if self.capture:
            self.capture.release()
            Clock.unschedule(self.update_frame)
