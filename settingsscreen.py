import os

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import OptionProperty, ObjectProperty, StringProperty, ListProperty, BooleanProperty, NumericProperty, DictProperty
from generalelements import TetraScreen, NormalPopup, save_current_crashlog
FileBrowser = None
from globals import default_c_left, default_c_right, default_c_rotate_l, default_c_rotate_r, default_c_down, default_c_drop, default_c_store, default_c_pause
from key_codes import keys

from kivy.lang.builder import Builder
Builder.load_string("""
<ControlScreen>:
    ScreenLayout:
        size_hint_y: 1
        orientation: 'vertical'
        Header:
            NormalButton:
                text: '  Back  '
                on_release: root.back()
            HeaderLabel:
                text: 'Buttons For '+root.control_name
            InfoLabel:
        BoxLayout:
            size_hint_y: 1
            padding: app.screen_border
            orientation: 'horizontal'
            Widget:
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: 1
                size_hint_x: None
                max_width: self.parent.height * .75
                width: self.parent.width if self.parent.width < self.max_width else self.max_width
                NormalRecycleView:
                    id: buttonView
                    data: root.buttons
                    viewclass: 'ControlElement'
                    RecycleBoxLayout:
                        padding: 40, 10
                        default_size: None, app.button_scale
                        default_size_hint: 1, None
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                WideButton:
                    text: "Add Button"
                    size_hint_y: None
                    height: app.button_scale
                    on_release: root.start_add_button()
            Widget:
    BoxLayout:
        canvas.before:
            Color:
                rgba: app.theme.darkened
            Rectangle:
                size: self.size
                pos: self.pos
        opacity: 1 if root.adding_button else 0
        NormalLabel:
            text: "Press Any Key..."

<ControlElement>:
    orientation: 'horizontal'
    LeftNormalLabel:
        text: root.button_name
    NormalButton:
        warn: True
        text: ' Remove '
        on_press: root.owner.delete_button(root.index)

<SettingsRow@BoxLayout>:
    padding: app.button_scale / 4, 0, app.button_scale / 2, 0
    orientation: 'horizontal'
    size_hint_y: None
    height: app.button_scale

<SettingsNormalLabel@NormalLabel>:
    font_size: app.text_scale * 1.5

<SettingsRowTint@SettingsRow>:
    canvas.before:
        Color:
            rgba: 0, 0, 0, 0.15
        Rectangle:
            size: self.size
            pos: self.pos
        Rectangle:
            pos: self.pos
            size: self.width, 2

<SettingsSpacer@Widget>:
    size_hint_y: None
    height: app.button_scale / 2

<AboutScreen>:
    ScreenLayout:
        orientation: 'vertical'
        Header:
            NormalButton:
                text: '  Back  '
                on_release: root.back()
            Widget:
            InfoLabel:
        BoxLayout:
            padding: app.screen_border
            Scroller:
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    Image:
                        source: 'data/icon.png'
                        size_hint_y: None
                        height: min(root.width * .5, root.height * .5)
                    Image:
                        source: 'data/appname.png'
                        size_hint_y: None
                        height: app.button_scale * 2
                    NormalLabel:
                        size_hint_y: None
                        height: app.button_scale / 2
                        text: 'Programmed in Python'
                    NormalLabel:
                        size_hint_y: None
                        height: app.button_scale / 2
                        text: 'Artwork created in Blender'
                    NormalLabel:
                        size_hint_y: None
                        height: app.button_scale / 2
                        text: 'Built on the Kivy framework'
                    NormalLabel:
                        size_hint_y: None
                        height: app.button_scale / 2
                        text: 'Music written in Open Modplug Tracker'
                    NormalLabel:
                        size_hint_y: None
                        height: app.button_scale / 2
                        text: 'Created by:'
                    NormalLabel:
                        size_hint_y: None
                        height: app.button_scale / 2
                        text: 'Hudson Barkley (Snu/snuq/Aritodo)'
                    NormalLabel:
                        size_hint_y: None
                        height: app.button_scale / 2
                        text: 'In 2020'
                    NormalLabel:
                        size_hint_y: None
                        height: app.button_scale / 2
                        text: ''
                    NormalLabel:
                        size_hint_y: None
                        height: app.button_scale / 2
                        text: "Theme A music written and performed by:"
                    NormalLabel:
                        size_hint_y: None
                        height: app.button_scale / 2
                        text: "Arjun Somvanshi"
                    NormalLabel:
                        size_hint_y: None
                        height: app.button_scale / 2
                        text: ''
                    NormalLabel:
                        size_hint_y: None
                        height: app.button_scale / 2
                        text: "Special thanks to:"
                    NormalLabel:
                        size_hint_y: None
                        height: app.button_scale / 2
                        text: "Arjun Somvanshi for advice and beta testing."
                    NormalLabel:
                        size_hint_y: None
                        height: app.button_scale / 2
                        text: ''
                    NormalLabel:
                        size_hint_y: None
                        height: app.button_scale / 2
                        text: "The very talented programmers"
                    NormalLabel:
                        size_hint_y: None
                        height: app.button_scale / 2
                        text: "who created the Kivy library."
                    NormalLabel:
                        size_hint_y: None
                        height: app.button_scale / 2
                        text: ''
                    NormalLabel:
                        size_hint_y: None
                        height: app.button_scale / 2
                        text: "Everyone who hangs out on the Kivy"
                    NormalLabel:
                        size_hint_y: None
                        height: app.button_scale / 2
                        text: "discord and has offered help and support."
                    NormalLabel:
                        size_hint_y: None
                        height: app.button_scale / 2
                        text: ''
                    NormalLabel:
                        size_hint_y: None
                        height: app.button_scale / 2
                        text: 'And of course, Alexey Pajitnov'
                    NormalLabel:
                        size_hint_y: None
                        height: app.button_scale / 2
                        text: ''

<SettingsScreen>:
    ScreenLayout:
        orientation: 'vertical'
        Header:
            NormalButton:
                text: '  Back  '
                on_release: root.back()
            HeaderLabel:
                text: 'Settings'
            InfoLabel:
        BoxLayout:
            padding: app.screen_border
            Scroller:
                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_x: 1
                    size_hint_y: None
                    height: self.minimum_height
                    Widget:
                    BoxLayout:
                        size_hint_x: None
                        max_width: root.height * .8
                        width: self.parent.width if self.parent.width < self.max_width else self.max_width
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        SettingsRow:
                            WideButton:
                                text: "About This App"
                                on_release: app.about()
                        SettingsRow:
                            disabled: False if app.has_crashlog else True
                            height: 0 if self.disabled else app.button_scale
                            opacity: 0 if self.disabled else 1
                            WideButton:
                                helptext: ['Save Crashlog:', '-', 'If this app crashes, it will save a copy of the information about the crash to a text file.  This button allows you to save a copy of the log in a more easy-to-access location so it can be used for debugging or sent to the developer.  ']
                                text: "Save Crashlog From "+app.crashlog_date
                                on_release: root.save_crashlog()
                        SettingsRow:
                            WideButton:
                                helptext: ['Reset Settings:', '-', 'This will reset the settings on this screen to their defaults.  Custom controls are not reset, high scores are not cleared.  ']
                                text: 'Reset Settings'
                                on_release: app.reset_settings()
                        SettingsRow:
                            WideButton:
                                helptext: ['Reset Controls:', '-', 'This button will reset the keyboard and joystick controls to the default settings, removing any custom configuration.  ']
                                text: "Reset All Controls"
                                on_release: root.reset_controls()
                        SettingsRow:
                            WideButton:
                                helptext: ['Clear High Scores:', '-', 'Delete all high score saved data shown on the main screen, including both marathon and sprint high scores.  ']
                                text: "Clear High Scores"
                                on_release: app.clear_scores()
                        SettingsSpacer:
                        SettingsRowTint:
                            SettingsNormalLabel:
                                text: 'Gameplay Settings'
                        SettingsRow:
                            LeftNormalLabel:
                                text: 'Show Piece Shadows:'
                            WideToggle:
                                size_hint_x: 0.5
                                text: 'Show' if app.piece_shadow else 'Hide'
                                state: 'down' if app.piece_shadow else 'normal'
                                on_release: app.piece_shadow = not app.piece_shadow
                                helptext: ['Show Piece Shadows:', '-', "Displays a partially transparent 'shadow' of the currently active piece where it will fall if dropped.  "]
                        SettingsRow:
                            LeftNormalLabel:
                                text: 'Play Sound Effects:'
                            WideToggle:
                                size_hint_x: 0.5
                                helptext: ['Play Sound Effects:', '-', "Set this to 'Silence' to mute sound effects in both the menu and in gameplay.  Music can still be played.  "]
                                text: 'Play' if app.sound_effects else 'Silence'
                                state: 'down' if app.sound_effects else 'normal'
                                on_release: app.sound_effects = not app.sound_effects
                        SettingsRow:
                            LeftNormalLabel:
                                text: 'SFX Volume:'
                                size_hint_x: 0.5
                            NormalSlider:
                                helptext: ['SFX Volume:', '-', 'The volume level for all sound effects both in menu and in game.  ']
                                min: 0
                                max: 1
                                value: app.volume
                                on_value: app.volume = self.value
                        SettingsRow:
                            height: app.button_scale if app.music_support else 0
                            opacity: 1 if app.music_support else 0
                            disabled: False if app.music_support else True
                            LeftNormalLabel:
                                text: 'Music Volume:'
                                size_hint_x: 0.5
                            NormalSlider:
                                helptext: ['Music Volume:', '-', 'The volume level for music while playing the game.  ']
                                min: 0
                                max: 1
                                value: app.music_volume
                                on_value: app.music_volume = self.value
                        SettingsRow:
                            LeftNormalLabel:
                                text: 'Theme:'
                                size_hint_x: 0.5
                            NormalInput:
                                text: app.theme_folder
                                disabled: True
                            NormalButton:
                                helptext: ['Browse For A Theme:', '-', 'Click this button to open the file browser to select a theme.  ', "Themes can include colors, piece graphics, background graphics, sound effects and music.  ", "You can load a folder with just music files (.mp3 or .ogg) to replace the music selections only."]
                                text: '  Browse  '
                                on_press: root.browse_theme()
                            NormalButton:
                                helptext: ['Remove Theme:', '-', 'This button will remove the currently selected theme setting and set it back to the default.']
                                text: '  X  '
                                warn: True
                                on_release: root.clear_theme()

                        SettingsSpacer:
                        SettingsRowTint:
                            SettingsNormalLabel:
                                text: 'Performance Settings'
                        SettingsRow:
                            LeftNormalLabel:
                                text: "Play Piece Animations:"
                            WideToggle:
                                helptext: ['Play Piece Animations:', '-', "When set to 'Play', the pieces will smoothly rotate, fall, and slide left and right.  Disable this for a more 'classic' feel.  "]
                                size_hint_x: 0.5
                                text: 'Play' if app.piece_animations else "Don't Play"
                                state: 'down' if app.piece_animations else 'normal'
                                on_release: app.piece_animations = not app.piece_animations
                        SettingsRow:
                            LeftNormalLabel:
                                text: "Line Animations Complexity:"
                            WideToggle:
                                helptext: ['Line Animation Complexity:', '-', "Set this to 'Full' for a variety of special effects when clearing lines.  Set to 'Simple' for a basic fade-out that will be easier on slower devices.  "]
                                size_hint_x: 0.5
                                text: 'Full' if app.line_animations else "Simple"
                                state: 'down' if app.line_animations else 'normal'
                                on_release: app.line_animations = not app.line_animations

                        SettingsSpacer:
                        SettingsRowTint:
                            SettingsNormalLabel:
                                text: 'Button Controls Settings'
                        SettingsRow:
                            LeftNormalLabel:
                                size_hint_x: .5
                                text: 'Move Left:'
                            WideButton:
                                text: root.m_left
                                on_release: root.set_buttons('m_left')
                        SettingsRow:
                            LeftNormalLabel:
                                size_hint_x: .5
                                text: 'Move Right:'
                            WideButton:
                                text: root.m_right
                                on_release: root.set_buttons('m_right')
                        SettingsRow:
                            LeftNormalLabel:
                                size_hint_x: .5
                                text: 'Rotate Left:'
                            WideButton:
                                text: root.m_rotate_l
                                on_release: root.set_buttons('m_rotate_l')
                        SettingsRow:
                            LeftNormalLabel:
                                size_hint_x: .5
                                text: 'Rotate Right:'
                            WideButton:
                                text: root.m_rotate_r
                                on_release: root.set_buttons('m_rotate_r')
                        SettingsRow:
                            LeftNormalLabel:
                                size_hint_x: .5
                                text: 'Move Down:'
                            WideButton:
                                text: root.m_down
                                on_release: root.set_buttons('m_down')
                        SettingsRow:
                            LeftNormalLabel:
                                size_hint_x: .5
                                text: 'Instant Drop:'
                            WideButton:
                                text: root.m_drop
                                on_release: root.set_buttons('m_drop')
                        SettingsRow:
                            LeftNormalLabel:
                                size_hint_x: .5
                                text: 'Store/Recall:'
                            WideButton:
                                text: root.m_store
                                on_release: root.set_buttons('m_store')
                        SettingsRow:
                            LeftNormalLabel:
                                size_hint_x: .5
                                text: 'Pause/Resume:'
                            WideButton:
                                text: root.m_pause
                                on_release: root.set_buttons('m_pause')
                        SettingsRow:
                            LeftNormalLabel:
                                size_hint_x: .5
                                text: 'Joystick Deadzone:'
                            NormalSlider:
                                helptext: ['Joystick Deadzone:', '-', 'This value represents the percentage of the joystick axis that is ignored before a button press is triggered.  Only applies to joysticks, not buttons or D-Pads']
                                min: 0
                                max: 1
                                value: app.deadzone
                                on_value: app.deadzone = self.value
                        SettingsSpacer:
                        SettingsRowTint:
                            SettingsNormalLabel:
                                text: "Touch Cotrols Settings"
                        SettingsRow:
                            disabled: not app.vibrator
                            opacity: 0 if self.disabled else 1
                            height: 0 if self.disabled else app.button_scale
                            LeftNormalLabel:
                                text: 'Haptic Feedback:'
                            WideToggle:
                                helptext: ['Haptic Feedback:', '-', 'When this is enabled, your device will vibrate when a piece collides with the walls or block stack, or when lines are completed.  ']
                                size_hint_x: 0.5
                                text: "No Vibrate" if self.state == 'normal' else 'Vibrate'
                                state: 'down' if app.vibration else 'normal'
                                on_state: app.vibration = not app.vibration
                        SettingsRow:
                            LeftNormalLabel:
                                text: 'Play Area Tap:'
                            WideToggle:
                                helptext: ['Play Area Tap Mode:', '-', 'Rotate:', 'Tapping the play field on the left or right side will cause the current piece to rotate left or right.  ', '', 'Slide:', 'Tapping the play field on the left or right side will cause the current piece to slide left or right.']
                                size_hint_x: 0.5
                                text: "Rotate" if self.state == 'normal' else 'Slide'
                                state: 'down' if app.play_tap else 'normal'
                                on_state: app.play_tap = not app.play_tap
                        SettingsRow:
                            LeftNormalLabel:
                                text: 'Play Area Swipe:'
                            WideToggle:
                                helptext: ['Play Area Swipe Mode:', '-', 'Rotate:', 'Swiping the play field left or right will cause the current piece to rotate left or right.  ', '', 'Slide:', 'Swiping the play field left or right will cause the current piece to slide left or right.']
                                size_hint_x: 0.5
                                text: "Slide" if self.state == 'normal' else 'Rotate'
                                state: 'down' if app.play_swipe else 'normal'
                                on_state: app.play_swipe = not app.play_swipe
                        SettingsRow:
                            LeftNormalLabel:
                                text: "Swipe Down To Drop:"
                            WideToggle:
                                helptext: ['Swipe Down To Drop:', '-', 'When enabled, swiping down on the play field will cause the current piece to hard drop.  When disabled, swiping down will not do anything.  ']
                                size_hint_x: 0.5
                                text: 'Enable' if app.swipe_vertical else 'Disable'
                                state: 'down' if app.swipe_vertical else 'normal'
                                on_release: app.swipe_vertical = not app.swipe_vertical
                        SettingsRow:
                            LeftNormalLabel:
                                text: 'Show Touch Buttons:'
                            WideToggle:
                                helptext: ['Show Touch Buttons:', '-', 'Show Buttons at the bottom of the game screen for controlling the current piece.  It is recommended to enable these when using a touch screen device.  ']
                                size_hint_x: 0.5
                                text: 'Show' if app.touch_area else 'Hide'
                                state: 'down' if app.touch_area else 'normal'
                                on_release: app.touch_area = not app.touch_area
                        SettingsRow:
                            LeftNormalLabel:
                                text: 'Touch Scale:'
                                size_hint_x: 0.5
                            NormalSlider:
                                helptext: ['Touch Scale:', '-', 'Set the overall size of the touch buttons with this slider.  For larger touch screen devices, it can be easier to use the touch controls if they are decreased in size.  ']
                                min: 0
                                max: 1
                                value: app.touch_scale
                                on_value: app.touch_scale = self.value

                        SettingsRow:
                            disabled: not app.touch_area
                            LeftNormalLabel:
                                text: 'Show Touch Rotate Buttons:'
                            WideToggle:
                                helptext: ['Show Touch Rotate Buttons:', '-', "When the touch buttons are enabled, set this to 'Show' to enable the buttons for rotating the piece left and right.  Disable this if you prefer to use taps or swipes on the play field for rotating the piece.  "]
                                size_hint_x: 0.5
                                text: 'Show' if app.touch_rotate else 'Hide'
                                state: 'down' if app.touch_rotate else 'normal'
                                on_release: app.touch_rotate = not app.touch_rotate
                        SettingsRow:
                            disabled: not app.touch_area
                            LeftNormalLabel:
                                text: 'Show Touch Slide Buttons:'
                            WideToggle:
                                helptext: ['Show Touch Slide Buttons:', '-', "When the touch buttons are enabled, set this to 'Show' to enable the buttons for sliding the piece left and right.  Disable this if you prefer to use taps or swipes on the play field for moving the piece.  "]
                                size_hint_x: 0.5
                                text: 'Show' if app.touch_slide else 'Hide'
                                state: 'down' if app.touch_slide else 'normal'
                                on_release: app.touch_slide = not app.touch_slide
                        SettingsRow:
                            LeftNormalLabel:
                                text: 'Touch Tap Time (Seconds):'
                            FloatInput:
                                helptext: ['Touch Tap Time:', '-', 'When using touch controls on the play field, holding a touch for longer than this period of time will start sliding the piece to the touch position.  Setting this too low will make it difficult to trigger the rotate or move left/right action, and setting it too high will make it more difficult to move the piece by dragging it.  ']
                                size_hint_x: 0.5
                                text: str(app.rotate_time)
                                on_text: root.set_rotate_time(self.text)
                        SettingsRow:
                            LeftNormalLabel:
                                text: "Border Size:"
                                size_hint_x: 0.5
                            NormalSlider:
                                helptext: ['Border Size:', '-', 'When using touch controls, devices without a bezel or with a case can be difficult to touch on the edge of the screen.  If you have this problem, try adjusting this slider up to add a padding around the edge of the screen.  ']
                                min: 0
                                max: 50
                                value: app.screen_border
                                on_value: app.screen_border = int(self.value)
                    Widget:
""")


def button_name(key):
    """Returns the correct name of a button or key based on the given keycode"""
    if key in keys:
        return keys[key]
    elif key <= 0:
        return "Button "+str(0 - key)
    else:
        return str(key)


class AboutScreen(TetraScreen):
    """Displays information about this app"""

    def on_enter(self):
        app = App.get_running_app()
        app.clear_selected_overlay()

    def back(self):
        app = App.get_running_app()
        app.screen_manager.transition.direction = 'down'
        app.screen_manager.current = 'settings'


class SettingsScreen(TetraScreen):
    """Displays and edits various app settings"""

    m_left = StringProperty()
    m_right = StringProperty()
    m_down = StringProperty()
    m_rotate_l = StringProperty()
    m_rotate_r = StringProperty()
    m_drop = StringProperty()
    m_store = StringProperty()
    m_pause = StringProperty()
    popup = ObjectProperty(allownone=True)
    from_screen = StringProperty()
    remember_selected = ObjectProperty(allownone=True)

    def back(self):
        app = App.get_running_app()
        self.remember_selected = None
        if self.from_screen:
            app.screen_manager.transition.direction = 'down'
            app.screen_manager.current = self.from_screen
            if self.from_screen == 'game':
                app.game_screen.resume_pause()
        else:
            app.main(direction='down')

    def dismiss(self):
        app = App.get_running_app()
        return app.dismiss_popup()

    def on_enter(self):
        app = App.get_running_app()
        app.clear_selected_overlay()
        self.update_buttons()
        if self.remember_selected is not None:
            app.set_selected_overlay(self.remember_selected)

    def on_leave(self):
        app = App.get_running_app()
        app.save_config()

    def set_buttons(self, control_name):
        app = App.get_running_app()
        self.remember_selected = app.selected_object
        app.control_settings(control_name)

    def set_rotate_time(self, text):
        try:
            app = App.get_running_app()
            app.rotate_time = float(text)
        except:
            pass

    def set_deadzone(self, text):
        try:
            app = App.get_running_app()
            app.deadzone = int(text)
        except:
            pass

    def reset_controls(self):
        app = App.get_running_app()
        app.m_left = default_c_left
        app.m_right = default_c_right
        app.m_rotate_l = default_c_rotate_l
        app.m_rotate_r = default_c_rotate_r
        app.m_down = default_c_down
        app.m_drop = default_c_drop
        app.m_store = default_c_store
        app.m_pause = default_c_pause
        app.deadzone = 1000
        app.rotate_time = 0.15
        self.update_buttons()

    def update_buttons(self):
        app = App.get_running_app()
        self.m_left = self.buttons_string(app.m_left)
        self.m_right = self.buttons_string(app.m_right)
        self.m_rotate_l = self.buttons_string(app.m_rotate_l)
        self.m_rotate_r = self.buttons_string(app.m_rotate_r)
        self.m_down = self.buttons_string(app.m_down)
        self.m_drop = self.buttons_string(app.m_drop)
        self.m_store = self.buttons_string(app.m_store)
        self.m_pause = self.buttons_string(app.m_pause)

    def buttons_string(self, keycodes):
        button_names = []
        for key in keycodes:
            button_names.append(button_name(key))
        return ', '.join(button_names)

    def clear_theme(self):
        app = App.get_running_app()
        if app.theme_folder:
            app.theme_folder = ''
            app.load_sounds()
            app.background_image = app.get_theme_folder()+'/background.png'
            app.load_theme()

    def browse_theme(self):
        app = App.get_running_app()
        global FileBrowser
        from filebrowser import FileBrowser
        app.dismiss_popup()
        content = FileBrowser(ok_text='Select', directory_select=True, edit_folders=False)
        content.bind(on_cancel=app.dismiss_popup)
        content.bind(on_ok=self.set_theme_folder)
        app.popup = NormalPopup(title="Select A Theme Folder", content=content, auto_dismiss=False)
        app.popup.open()

    def set_theme_folder(self, answer):
        app = App.get_running_app()
        path = app.popup.content.path
        app.dismiss_popup()
        if path:
            app.theme_folder = path
            app.load_theme()
            app.load_sounds()

    def save_crashlog(self):
        app = App.get_running_app()
        app.dismiss_popup()
        global FileBrowser
        from filebrowser import FileBrowser
        content = FileBrowser(ok_text='Save', directory_select=True, edit_folders=False)
        content.bind(on_cancel=app.dismiss_popup)
        content.bind(on_ok=self.save_crashlog_finish)
        app.popup = NormalPopup(title="Select A Location To Save Crashlog", content=content)
        app.popup.open()

    def save_crashlog_finish(self, answer):
        app = App.get_running_app()
        path = app.popup.content.path
        app.dismiss_popup()
        saved = False
        if path:
            saved = save_current_crashlog(path)
        if saved:
            app.message('Saved Crashlog')
        else:
            app.message('Could Not Save Crashlog!')


class ControlElement(BoxLayout):
    """Viewclass for displaying controls buttons"""

    button_name = StringProperty()
    index = NumericProperty()
    owner = ObjectProperty()


class ControlScreen(TetraScreen):
    """Screen for displaying and setting controls"""

    control = StringProperty()
    control_name = StringProperty()
    buttons = ListProperty()
    button_codes = ListProperty()
    adding_button = BooleanProperty(False)

    def back(self):
        self.dismiss()

    def on_enter(self):
        app = App.get_running_app()
        app.clear_selected_overlay()
        app.multiplayer_stop()

    def dismiss(self):
        app = App.get_running_app()
        app.screen_manager.transition.direction = 'down'
        app.screen_manager.current = 'settings'
        return True

    def key(self, key, down):
        if self.adding_button and down:
            self.adding_button = False
            if key not in self.button_codes:
                self.button_codes.append(key)
                self.refresh_buttons()
        else:
            super().key(key, down)

    def start_add_button(self):
        self.adding_button = True

    def delete_button(self, index):
        self.button_codes.pop(index)
        self.refresh_buttons()

    def on_pre_enter(self):
        app = App.get_running_app()
        self.adding_button = False
        if self.control == 'm_left':
            self.control_name = 'Move Left'
        elif self.control == 'm_right':
            self.control_name = 'Move Right'
        elif self.control == 'm_rotate_l':
            self.control_name = 'Rotate Left'
        elif self.control == 'm_rotate_r':
            self.control_name = 'Rotate Right'
        elif self.control == 'm_down':
            self.control_name = 'Move Down'
        elif self.control == 'm_drop':
            self.control_name = 'Hard Drop'
        elif self.control == 'm_store':
            self.control_name = 'Store Piece'
        elif self.control == 'm_pause':
            self.control_name = 'Pause'
        self.button_codes = getattr(app, self.control)
        self.refresh_buttons()

    def refresh_buttons(self):
        self.buttons = []
        for index, code in enumerate(self.button_codes):
            button_data = {
                'button_name': button_name(code),
                'index': index,
                'owner': self
            }
            self.buttons.append(button_data)

    def on_pre_leave(self):
        app = App.get_running_app()
        setattr(app, self.control, self.button_codes)
        app.save_config()
