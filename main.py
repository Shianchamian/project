import sqlite3
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import MDList, IconRightWidget, TwoLineAvatarIconListItem, ImageLeftWidget
from kivymd.uix.screen import Screen
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.core.window import Window
from kivymd.uix.navigationdrawer import MDNavigationDrawer
from kivy.uix.screenmanager import ScreenManager
from kivy.metrics import dp
from ManageFace import init_db, manage_face, delete_face
from AddFace import AddFaceScreen
from Recognition import RecognitionScreen
from helpers import screen_helper
from insightface.app import FaceAnalysis
from utils.voice_manager import VoiceManager


class MainScreen(Screen):
    pass


class MyApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.face_model = FaceAnalysis(name="buffalo_s")
        self.face_model.prepare(ctx_id=-1)
        # 初始化语音管理器
        self.voice_manager = VoiceManager()

    def build(self):
        """Initialize the app, set theme, load screens, and set default screen."""
        self.theme_cls.primary_palette = 'Teal'
        screen = Builder.load_string(screen_helper)
        screen.current = 'main'  # Default screen
        init_db()  # Ensure database is initialized
        return screen

    def go_home(self):
        """Return to the main screen and reset the content area."""
        main_screen = self.root.get_screen('main')
        content_area = main_screen.ids.content_area
        content_area.clear_widgets()  # Clear previous content

        content_area.add_widget(MDLabel(
            text="Welcome!",
            halign="center",
            font_style="H5",
            theme_text_color="Primary"
        ))

        self.root.current = 'main'

    def add_face(self):
        """Switch to the face registration screen."""
        self.clean_content()
        self.root.current = 'add_face'

    def recognize_face(self):
        """Switch to the face recognition screen."""
        self.clean_content()
        self.root.current = 'recognize'

    def manage_face(self):
        """Display stored face records from the database."""
        self.clean_content()

        faces = manage_face()  # Fetch data

        if not faces:
            self.root.get_screen('main').ids.content_area.add_widget(
                MDLabel(text="No face data found.", halign="center", theme_text_color="Secondary")
            )
            return

        # Create ScrollView and List
        scroll_view = ScrollView()
        md_list = MDList()

        for face_id, name, relation, image_path in faces:
            item = TwoLineAvatarIconListItem(text=name, secondary_text=relation)

            # Use default avatar if no image is available
            avatar = ImageLeftWidget(source=image_path if image_path else "assets/default_face.png")
            item.add_widget(avatar)

            # Add delete button
            delete_btn = IconRightWidget(icon="delete")
            delete_btn.bind(on_release=lambda x, fid=face_id: self.confirm_delete(fid))
            item.ids._right_container.add_widget(delete_btn)

            md_list.add_widget(item)

        scroll_view.add_widget(md_list)
        self.root.get_screen('main').ids.content_area.add_widget(scroll_view)

    def confirm_delete(self, face_id):
        """Show confirmation dialog before deleting a face record."""
        # 获取要删除的人名
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM faces WHERE id=?", (face_id,))
        name = cursor.fetchone()[0]
        conn.close()
        
        # 构建确认消息
        confirm_text = f"Are you sure you want to delete {name}'s face?"
        
        # 播放语音提示
        self.voice_manager.speak(confirm_text)
        
        self.dialog = MDDialog(
            title="Confirm Delete",
            text=confirm_text,
            buttons=[
                MDRaisedButton(
                    text="Cancel", 
                    on_release=lambda x: self.cancel_delete()
                ),
                MDFlatButton(
                    text="Delete", 
                    on_release=lambda x: self.delete_face(face_id, name)
                )
            ]
        )
        self.dialog.open()

    def cancel_delete(self):
        """取消删除操作"""
        self.voice_manager.speak("Operation cancelled")
        self.dialog.dismiss()

    def delete_face(self, face_id, name):
        """Delete a face record from the database and refresh the UI."""
        self.voice_manager.speak(f"Deleted {name}'s face")
        delete_face(face_id)
        self.dialog.dismiss()
        self.manage_face()

    def clean_content(self):
        """Clear the main screen content area before updating."""
        main_screen = self.root.get_screen('main')
        content_area = main_screen.ids.content_area
        content_area.clear_widgets()

    def on_tab_press(self, tab_name):
        """Handle bottom navigation tab selection."""
        if tab_name == 'recognize':
            self.recognize_face()
        elif tab_name == 'add':
            self.add_face()
        elif tab_name == 'db':
            self.manage_face()


if __name__ == "__main__":
    MyApp().run()
