import os

from kivy.app import App
from kivy.properties import AliasProperty, ObjectProperty, StringProperty, ListProperty, BooleanProperty, NumericProperty, DictProperty
from generalelements import TetraScreen, IndexToggle

from kivy.lang.builder import Builder
Builder.load_string("""
<SprintScreen>:
    first_selected: first_select if not first_select.disabled else second_select
    ScreenLayout:
        pos: root.pos
        size: root.size
        size_hint: None, None
        orientation: 'vertical'
        Header:
            NormalButton:
                text: '  Back  '
                on_release: root.back()
            HeaderLabel:
                text: 'Sprint'
            SettingsButton:
                on_release: app.show_settings('sprint')
        BoxLayout:
            padding: app.screen_border
            orientation: 'vertical'
            LayoutSplitter:
                owner: root
                WideButton:
                    id: first_select
                    font_size: app.text_scale * 1.5
                    size_hint_y: None
                    size_hint_x: 1 if app.pause_data else 0.001
                    height: app.button_scale * 1.5 if app.pause_data else 0
                    opacity: 1 if app.pause_data else 0
                    disabled: False if app.pause_data else True
                    text: 'Resume Game'
                    on_release: app.resume_game()
                WideButton:
                    id: second_select
                    font_size: app.text_scale * 1.5
                    size_hint_y: None
                    height: app.button_scale * 1.5
                    text: 'Start Game'
                    on_release: root.start_game()
            LayoutSplitter:
                owner: root
                size_hint_y: 1
                GridLayout:
                    size_hint_y: None
                    height: self.parent.height if self.parent.wider else self.minimum_height
                    cols: 1
                    padding: app.button_scale / 2, 0
                    Widget:
                        size_hint_y: None
                        height: 0 if self.parent.parent.wider else (app.button_scale / 4)
                    LeftNormalLabel:
                        size_hint_y: None
                        height: app.button_scale if self.parent.parent.wider else (app.button_scale / 2)
                        text: "Game Speed:"
                    SmoothSetting:
                        helptext: ['Game Speed:', '-', 'This defines the starting speed level for your game.  Lines completed will increase your level, but your speed will not increase until you surpass this starting level.  ']
                        size_hint_y: None
                        height: app.button_scale * .75
                        item_width: app.button_scale
                        control_width: app.button_scale * 0.75
                        start_on: root.speed
                        on_active: root.speed = self.active
                        content: ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15']
                    LeftNormalLabel:
                        size_hint_y: None
                        height: app.button_scale if self.parent.parent.wider else (app.button_scale / 2)
                        text: "Filled Lines:"
                    SmoothSetting:
                        helptext: ['Filled Lines:', '-', 'This sets a number of lines to be filled with garbage blocks at the start of the game.  For each level of filled lines, two garbage lines will be added to the bottom of the field.  ']
                        size_hint_y: None
                        height: app.button_scale * .75
                        item_width: app.button_scale
                        control_width: app.button_scale * 0.75
                        start_on: root.filled
                        on_active: root.filled = self.active
                        content: ['0', '1', '2', '3', '4', '5', '6', '7']
                    LeftNormalLabel:
                        size_hint_y: None
                        height: app.button_scale if self.parent.parent.wider else (app.button_scale / 2)
                        text: "Lines to Complete:"
                    SmoothSetting:
                        helptext: ['Lines to Complete:', '-', 'In a sprint type game, the goal is to complete this number of lines.  Once you reach this goal, the game will end.']
                        size_hint_y: None
                        height: app.button_scale * .75
                        item_width: app.button_scale
                        control_width: app.button_scale * 0.75
                        start_on: root.length
                        on_active: root.length = self.active
                        content: ['25', '50', '75', '100']
                BoxLayout:
                    orientation: 'vertical'
                    padding: app.button_scale / 2, 0
                    LeftNormalLabel:
                        size_hint_y: None
                        height: (app.button_scale if self.parent.parent.wider else (app.button_scale / 2)) if app.music_support else 0
                        opacity: 1 if app.music_support else 0
                        text: "Music:"
                    Scroller:
                        size_hint: 1, 1
                        do_scroll_x: False
                        do_scroll_y: True
                        BoxLayout:
                            id: music
                            orientation: 'vertical'
                            size_hint_y: None
                            height: self.minimum_height if app.music_support else 0
                            opacity: 1 if app.music_support else 0

<MarathonScreen>:
    first_selected: first_select if not first_select.disabled else second_select
    ScreenLayout:
        pos: root.pos
        size: root.size
        size_hint: None, None
        orientation: 'vertical'
        Header:
            NormalButton:
                text: '  Back  '
                on_release: root.back()
            HeaderLabel:
                text: 'Marathon'
            SettingsButton:
                on_release: app.show_settings('marathon')
        BoxLayout:
            padding: app.screen_border
            orientation: 'vertical'
            LayoutSplitter:
                owner: root
                WideButton:
                    id: first_select
                    font_size: app.text_scale * 1.5
                    size_hint_y: None
                    size_hint_x: 1 if app.pause_data else 0.001
                    height: app.button_scale * 1.5 if app.pause_data else 0
                    opacity: 1 if app.pause_data else 0
                    disabled: False if app.pause_data else True
                    text: 'Resume Game'
                    on_release: app.resume_game()
                WideButton:
                    id: second_select
                    font_size: app.text_scale * 1.5
                    size_hint_y: None
                    height: app.button_scale * 1.5
                    text: 'Start Game'
                    on_release: root.start_game()
            LayoutSplitter:
                owner: root
                size_hint_y: 1
                GridLayout:
                    size_hint_y: None
                    height: self.parent.height if self.parent.wider else self.minimum_height
                    cols: 1
                    padding: app.button_scale / 2, 0
                    Widget:
                        size_hint_y: None
                        height: 0 if self.parent.parent.wider else (app.button_scale / 4)
                    LeftNormalLabel:
                        size_hint_y: None
                        height: app.button_scale if self.parent.parent.wider else (app.button_scale / 2)
                        text: "Game Speed:"
                    SmoothSetting:
                        helptext: ['Game Speed:', '-', 'This defines the starting speed level for your game.  Lines completed will increase your level, but your speed will not increase until you surpass this starting level.  ']
                        size_hint_y: None
                        height: app.button_scale * .75
                        item_width: app.button_scale
                        control_width: app.button_scale * 0.75
                        start_on: root.speed
                        on_active: root.speed = self.active
                        content: ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15']
                    LeftNormalLabel:
                        size_hint_y: None
                        height: app.button_scale if self.parent.parent.wider else (app.button_scale / 2)
                        text: "Filled Lines:"
                    SmoothSetting:
                        helptext: ['Filled Lines:', '-', 'This sets a number of lines to be filled with garbage blocks at the start of the game.  For each level of filled lines, two garbage lines will be added to the bottom of the field.  ']
                        size_hint_y: None
                        height: app.button_scale * .75
                        item_width: app.button_scale
                        control_width: app.button_scale * 0.75
                        start_on: root.filled
                        on_active: root.filled = self.active
                        content: ['0', '1', '2', '3', '4', '5', '6', '7']
                    LeftNormalLabel:
                        size_hint_y: None
                        height: app.button_scale if self.parent.parent.wider else (app.button_scale / 2)
                        text: "Add Lines After Seconds:"
                    SmoothSetting:
                        helptext: ['Add Lines:', '-', 'When this is set to a value other than Off, a garbage line will be added to the bottom of the screen every few seconds.  ']
                        size_hint_y: None
                        height: app.button_scale * .75
                        item_width: app.button_scale * 2
                        control_width: app.button_scale * 0.75
                        start_on: root.add_lines
                        on_active: root.add_lines = self.active
                        content: ['Off', '45', '30', '20', '10', '7.5', '5']
                BoxLayout:
                    orientation: 'vertical'
                    padding: app.button_scale / 2, 0
                    LeftNormalLabel:
                        size_hint_y: None
                        height: (app.button_scale if self.parent.parent.wider else (app.button_scale / 2)) if app.music_support else 0
                        opacity: 1 if app.music_support else 0
                        text: "Music:"
                    Scroller:
                        size_hint: 1, 1
                        do_scroll_x: False
                        do_scroll_y: True
                        BoxLayout:
                            id: music
                            orientation: 'vertical'
                            size_hint_y: None
                            height: self.minimum_height if app.music_support else 0
                            opacity: 1 if app.music_support else 0
""")


class GameStartScreen(TetraScreen):
    """Base class for screens that feature settings for different game modes"""

    def on_enter(self):
        app = App.get_running_app()
        app.clear_selected_overlay()
        app.multiplayer_stop()
        self.populate_areas()

    def populate_music(self):
        app = App.get_running_app()
        music_area = self.ids['music']
        music_area.clear_widgets()
        for index, music in enumerate(app.musics):
            music_theme = music[0]
            if music_theme:
                music_name = os.path.splitext(music_theme)[0]
                music_button = IndexToggle(text=music_name, group='music', index=index)
            else:
                music_button = IndexToggle(text='None', group='music', index=index)
            if index == app.music_theme:
                music_button.state = 'down'
            music_button.bind(on_release=self.set_music)
            music_area.add_widget(music_button)

    def set_music(self, button):
        app = App.get_running_app()
        app.music_theme = button.index
        if button.state != 'down':
            button.state = 'down'
        if button.index == 0:
            app.stop_music()
        else:
            app.start_music()
            app.resume_music()

    def on_pre_leave(self):
        app = App.get_running_app()
        app.stop_music()


class MarathonScreen(GameStartScreen):
    """Screen for settings for a Marathon game"""

    speed = NumericProperty(0)  #Starting level
    filled = NumericProperty(0)  #Number of lines to fill with garbage
    add_lines = NumericProperty(0)

    def back(self):
        app = App.get_running_app()
        app.main()

    def populate_areas(self):
        self.populate_music()

    def start_game(self):
        app = App.get_running_app()
        app.game()
        game_screen = app.game_screen
        game_screen.start_speed = self.speed
        game_screen.start_filled = self.filled
        game_screen.periodic_add_lines = self.add_lines
        game_screen.game_mode = 'A'
        game_screen.start_game()


class SprintScreen(GameStartScreen):
    """Screen for settings for a Sprint game"""

    speed = NumericProperty(0)  #Starting level
    filled = NumericProperty(0)  #Number of lines to fill with garbage
    length = NumericProperty(0)  #Number of lines to clear to complete game

    def back(self):
        app = App.get_running_app()
        app.main()

    def populate_areas(self):
        self.populate_music()

    def start_game(self):
        app = App.get_running_app()
        app.game()
        game_screen = app.game_screen
        game_screen.start_speed = self.speed
        game_screen.start_filled = self.filled
        game_screen.start_length = (self.length + 1) * 25
        game_screen.periodic_add_lines = 0
        game_screen.game_mode = 'B'
        game_screen.start_game()
