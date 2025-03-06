screen_helper = """
ScreenManager:
    MainScreen:
    AddFaceScreen:
    RecognitionScreen:

<MainScreen>:
    name: 'main'
    MDNavigationLayout:
        ScreenManager:
            Screen:
                BoxLayout:
                    orientation: 'vertical'
                    MDTopAppBar:
                        # title: 'Face Recognition App'
                        right_action_items: [["refresh", lambda x: None],["home", lambda x: app.go_home()]] 
                        left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
                        elevation: 1
                        
                        widget:

                    BoxLayout:
                        id: content_area  
                        size_hint_y: 0.8
                        orientation: 'vertical'
                        padding: dp(20) 
                        spacing: dp(20)  
                        
                        MDLabel:
                            text: "Welcome!"
                            halign: "center"
                            font_style: "H5"
                            theme_text_color: "Primary"

                    MDBottomNavigation:
                        size_hint_y: 0.2
                        
                        MDBottomNavigationItem:
                            name: 'add'
                            icon: 'plus'
                            text: 'Add'
                            on_tab_press: app.on_tab_press('add')
                        MDBottomNavigationItem:
                            name: 'recognize'
                            icon: 'face-recognition'
                            text: 'Recognition'
                            on_tab_press: app.on_tab_press('recognize')

                        MDBottomNavigationItem:
                            name: 'database'
                            icon: 'database'
                            text: 'Faces'
                            on_tab_press: app.on_tab_press('db')

        MDNavigationDrawer:
            id: nav_drawer
            
            BoxLayout:
                orientation: 'vertical'
                widget:
                        
                ScrollView:
                    MDList:
                        OneLineIconListItem:
                            text: 'My Profile'
                            IconLeftWidget:
                                icon: 'account'

                        OneLineIconListItem:
                            text: 'How to use'
                            IconLeftWidget:
                                icon: 'help'


<AddFaceScreen>:
    name: 'add_face'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(10)

        MDIconButton:
            icon: 'arrow-left'
            on_release: root.manager.current = 'main'
            
        BoxLayout:
            id: camera_area
            height: dp(300)
            padding: dp(20)

<RecognitionScreen>:
    name: 'recognize'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(10)

        MDIconButton:
            icon: 'arrow-left'
            on_release: app.go_home()
"""
