import os

from kivy.app import App
from kivy.animation import Animation
from kivy.properties import OptionProperty, ObjectProperty, StringProperty, ListProperty, BooleanProperty, NumericProperty, DictProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior

from generalelements import TetraScreen, time_index

from globals import fps

from kivy.lang.builder import Builder
Builder.load_string("""
<ReplayElement>:
    on_release: root.load()
    canvas:
        Color:
            rgba: app.theme.button_up if self.state == 'normal' else app.theme.button_down
        BorderImage:
            display_border: [app.display_border, app.display_border, app.display_border, app.display_border]
            border: [16, 16, 16, 16]
            size: self.size
            pos: self.pos
            source: 'data/button.png'
    canvas.after:
        Color:
            rgba: app.overlay_color if app.selected_object == self else (1, 1, 1, 0)
        Rectangle:
            size: self.size
            pos: self.pos
    WideButton:
        size_hint: None, None
        size: app.button_scale, app.button_scale
        pos: root.pos[0] + root.width - app.button_scale, root.pos[1] + root.height - app.button_scale
        text: 'X'
        warn: True
        on_release: root.delete()
    BoxLayout:
        padding: app.button_scale / 2, app.button_scale / 4
        orientation: 'vertical'
        size: root.size
        pos: root.pos
        LeftNormalLabel:
            text: root.text
        LeftNormalLabel:
            text: root.date
        LeftNormalLabel:
            text: root.info

<ReplayScreen>:
    wider: True if self.width > self.height else False
    ScreenLayout:
        orientation: 'vertical'
        Header:
            NormalButton:
                text: '  Back  '
                on_release: root.back()
            HeaderLabel:
                text: 'Replays'
            InfoLabel:
            SettingsButton:
                on_release: app.show_settings('replay')
        Widget:
            size_hint_y: 0.01
        BoxLayout:
            padding: app.screen_border
            orientation: 'horizontal'
            Widget:
                size_hint_x: .25 if root.wider else 0.01
            BoxLayout:
                orientation: 'vertical'
                NormalRecycleView:
                    size_hint_x: None
                    size_hint_x: 1
                    orientation: 'vertical'
                    id: historyView
                    data: root.histories
                    viewclass: 'ReplayElement'
                    RecycleBoxLayout:
                        padding: app.button_scale / 2, 0, app.button_scale / 2, 0
                        spacing: 10
                        default_size: None, app.button_scale * 2
                        default_size_hint: 1, None
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                WideButton:
                    warn: True
                    size_hint_y: None
                    height: app.button_scale
                    text: 'Delete all replays'
                    on_release: app.clear_replays()
            Widget:
                size_hint_x: .25 if root.wider else 0.01
""")


class ReplayScreen(TetraScreen):
    """Screen for showing replays"""

    histories = ListProperty()

    def back(self):
        app = App.get_running_app()
        app.main()

    def on_enter(self):
        app = App.get_running_app()
        app.clear_selected_overlay()
        app.multiplayer_stop()
        self.update_histories()

    def update_histories(self):
        app = App.get_running_app()
        self.histories = []
        histories_folder = os.path.join(app.savefolder, 'histories')
        files = reversed(os.listdir(histories_folder))
        for file in files:
            filename, extension = os.path.splitext(file)
            if extension.lower() == '.txt':
                history_path = os.path.join(histories_folder, file)
                try:
                    with open(history_path, 'r') as history_file:
                        for index, line in enumerate(history_file):
                            if index == 0:
                                date_data = line.split(',')
                                date_year, date_month, date_day, date_hour, date_minute = date_data
                            elif index == 1:
                                length = int(line)
                            elif index == 2:
                                total_lines = line.strip()
                            elif index == 3:
                                total_pieces = line.strip()
                            elif index == 4:
                                score = line.strip()
                            else:
                                break
                    length_formatted = time_index(length/fps)
                    date_formatted = date_year+'-'+date_month+'-'+date_day+' '+date_hour+':'+date_minute
                    history_data = {
                        'file': history_path,
                        'text': filename,
                        'length': length_formatted,
                        'pieces': total_pieces,
                        'date': date_formatted,
                        'score': score,
                        'lines': total_lines,
                        'info': 'Score: '+score+', Time:'+length_formatted+', '+total_pieces+' pieces, '+total_lines+' lines'
                    }
                    self.histories.append(history_data)
                except:
                    pass
        #self.ids.historyView.data = self.histories


class ReplayElement(RecycleDataViewBehavior, ButtonBehavior, FloatLayout):
    """Viewclass for a replay on the ReplayScreen"""

    selectable_item = BooleanProperty(True)
    index = NumericProperty(0)
    text = StringProperty()
    file = StringProperty()
    date = StringProperty()
    length = StringProperty()
    pieces = StringProperty()
    score = StringProperty()
    info = StringProperty()
    animation = ObjectProperty(allownone=True)
    remove_length = NumericProperty(0.25)
    o_pos = ListProperty()
    o_opacity = NumericProperty()

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        return super().refresh_view_attrs(rv, index, data)

    def load(self):
        app = App.get_running_app()
        app.play_sound('button')
        app.replay_file(self.file)

    def delete(self):
        if not self.animation:
            self.o_pos = self.pos
            self.o_opacity = self.opacity
            self.animation = Animation(opacity=0, duration=self.remove_length, pos=(self.pos[0]-self.width, self.pos[1]))
            self.animation.start(self)
            self.animation.bind(on_complete=self.delete_finish)

    def delete_finish(self, *_):
        app = App.get_running_app()
        self.animation = None
        self.opacity = self.o_opacity
        self.pos = self.o_pos
        try:
            os.remove(self.file)
        except:
            pass
        app.replay_screen.update_histories()
