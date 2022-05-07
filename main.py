"""
todo:
    add help dialog to sliders
    multiplayer improvements:
        seems to freeze on unpause?
        compute a suggested handicap after each game (based on number of lines sent/received and block height at end)
"""
import time
startup_time = time.time()
from globals import *
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,disable_multitouch')
Config.set('graphics', 'maxfps', str(fps * 2))
import random
from datetime import datetime
import os
app_directory = os.path.dirname(os.path.realpath(__file__))
from kivy.logger import Logger
from kivy.core.window import Window
from kivy.base import EventLoop
from kivy.clock import Clock
from kivy.app import App
from kivy.animation import Animation
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.properties import OptionProperty, ObjectProperty, StringProperty, ListProperty, BooleanProperty, NumericProperty, DictProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.recycleview import RecycleView
from kivy.resources import resource_find
from generalelements import *
from globals import emotions_colors
from smoothsetting import SmoothSetting
from configparser import ConfigParser

#Multiplayer screen imports, delay until needed
Connector = None
socket = None

FileBrowser = None
if platform == 'win':
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
if platform == 'android':
    from plyer import vibrator
    from audio_android import SoundAndroid as SoundFX
    from audio_android import SoundAndroid as SoundMusic
else:
    vibrator = None
    from kivy.core.audio.audio_sdl2 import SoundSDL2 as SoundFX
    from kivy.core.audio.audio_sdl2 import MusicSDL2 as SoundMusic


class Theme(Widget):
    """Theme class that stores all the colors used in the interface."""
    #not used currently
    button_warn_down = ListProperty([0.78, 0.33, 0.33, 1.0])
    button_warn_up = ListProperty([1.0, 0.6, 0.6, 1.0])
    #Not Setable
    scroller = ListProperty([0.7, 0.7, 0.7, 0.388])
    scroller_selected = ListProperty([0.7, 0.7, 0.7, 0.9])
    info_text = ListProperty([0.0, 0.0, 0.0, 1.0])
    info_background = ListProperty([1.0, 1.0, 0.0, 0.75])
    darkened = ListProperty([0, 0, .1, .2])

    #Set By Theme
    button_down = ListProperty([1, 1, 1, 1])
    button_up = ListProperty([1, 1, 1, 1])
    button_text = ListProperty([1, 1, 1, 1])
    button_toggle_true = ListProperty([1, 1, 1, 1])
    button_toggle_false = ListProperty([1, 1, 1, 1])
    button_disabled = ListProperty([1, 1, 1, 1])
    button_disabled_text = ListProperty([1, 1, 1, 1])
    slider_background = ListProperty([1, 1, 1, 1])
    slider_grabber = ListProperty([1, 1, 1, 1])
    input_background = ListProperty([1, 1, 1, 1])

    header_background = ListProperty([1, 1, 1, 1])
    header_text = ListProperty([1, 1, 1, 1])
    text = ListProperty([1, 1, 1, 1])
    disabled_text = ListProperty([1, 1, 1, 1])
    selected = ListProperty([1, 1, 1, 1])
    indented = ListProperty([1, 1, 1, 1])
    background = ListProperty([1, 1, 1, 1])
    background_overlay = ListProperty([1, 1, 1, 1])
    background_column = ListProperty([1, 1, 1, 1])
    shadow_color = ListProperty([0, 0, 0, .15])

    I = ListProperty([1, 1, 1, 1])
    J = ListProperty([1, 1, 1, 1])
    L = ListProperty([1, 1, 1, 1])
    O = ListProperty([1, 1, 1, 1])
    S = ListProperty([1, 1, 1, 1])
    Z = ListProperty([1, 1, 1, 1])
    T = ListProperty([1, 1, 1, 1])


class MainScreenManager(ScreenManager):
    """Base screen manager class, holds the various game screens"""
    pass


class MainScreen(TetraScreen):
    """Screen that displays the main menu"""

    scores_a = ListProperty()
    scores_b = ListProperty()

    def on_enter(self):
        app.clear_selected_overlay()
        self.scores_a = []
        self.scores_b = []
        for score in app.scores_a:
            score_formatted = str(score[0])+'points '+str(score[1])+'lines '+score[2]
            self.scores_a.append({'text': score_formatted})
        for score in app.scores_b:
            score_formatted = str(score[0])+'points '+str(score[1])+'lines '+score[2]
            self.scores_b.append({'text': score_formatted})


class TouchArea(BoxLayout):
    image = StringProperty('')
    function = StringProperty('down')

    def on_touch_down(self, touch):
        if self.disabled:
            return
        game_screen = app.game_screen
        if game_screen is None:
            return
        if game_screen.paused or game_screen.replay or not game_screen.game_running:
            return
        if self.collide_point(*touch.pos):
            touch.grab(self)
            if self.function == 'down':
                game_screen.move_down()
                game_screen.move_down_touch()
            elif self.function == 'left':
                game_screen.move_left()
                game_screen.move_left_touch()
            elif self.function == 'right':
                game_screen.move_right()
                game_screen.move_right_touch()

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            game_screen = app.game_screen
            if game_screen is None:
                return
            if self.function == 'down':
                game_screen.move_down_touch_off()
            elif self.function == 'left':
                game_screen.move_left_touch_off()
            elif self.function == 'right':
                game_screen.move_right_touch_off()


class TouchControl(BoxLayout):
    delay_move = ObjectProperty(allownone=True)
    invisible = BooleanProperty(False)
    swipe_distance = 50
    swipe_down_distance = 100

    def on_touch_down(self, touch):
        game_screen = app.game_screen
        if game_screen is None:
            return
        if game_screen.paused or game_screen.replay or not game_screen.game_running:
            return
        if app.touch_area or self.invisible:
            if self.collide_point(*touch.pos):
                touch.grab(self)
                self.delay_move = Clock.schedule_once(lambda x: self.update_move(touch), app.rotate_time)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            touch_length = time.time() - touch.time_start
            if touch_length > app.rotate_time:
                self.update_move(touch)

    def update_move(self, touch):
        game_screen = app.game_screen
        if game_screen is None:
            return
        x_pos = touch.pos[0] - self.pos[0]
        touch_percent_x = x_pos / self.width
        if touch_percent_x < 0:
            touch_percent_x = 0
        elif touch_percent_x > 1:
            touch_percent_x = 1
        game_screen.move_x_percent(touch_percent_x)

    def on_touch_up(self, touch):
        if self.delay_move:
            self.delay_move.cancel()
            self.delay_move = None
        if touch.grab_current is self:
            touch.ungrab(self)
            game_screen = app.game_screen
            if game_screen is None:
                return
            game_screen.move_x_percent_off()
            touch_length = touch.time_end - touch.time_start
            if touch_length <= app.rotate_time:
                x_delta = touch.opos[0] - touch.pos[0]
                y_delta = touch.opos[1] - touch.pos[1]
                swiped = False
                if abs(x_delta) > abs(y_delta):
                    if x_delta > self.swipe_distance:
                        #swipe left
                        swiped = True
                        if app.play_swipe:
                            game_screen.rotate_left()
                        else:
                            game_screen.move_left()
                    elif x_delta < 0 - self.swipe_distance:
                        #swipe right
                        swiped = True
                        if app.play_swipe:
                            game_screen.rotate_right()
                        else:
                            game_screen.move_right()
                elif app.swipe_vertical:
                    if y_delta > self.swipe_down_distance:
                        #swipe down
                        swiped = True
                        game_screen.hard_down()
                    elif y_delta < 0 - self.swipe_down_distance:
                        #swipe up
                        swiped = True
                        #game_screen.store()
                if not swiped:
                    x_pos = touch.pos[0] - self.pos[0]
                    touch_percent_x = x_pos / self.width
                    if not app.play_tap:
                        if touch_percent_x < 0.5:
                            game_screen.rotate_left()
                        else:
                            game_screen.rotate_right()
                    else:
                        if touch_percent_x < 0.5:
                            game_screen.move_left()
                        else:
                            game_screen.move_right()


class TouchButton(ButtonBehavior, BoxLayout):
    image = StringProperty('')

    def on_touch_down(self, touch):
        game_screen = app.game_screen
        if game_screen is None:
            return
        if game_screen.paused or game_screen.replay or not game_screen.game_running:
            return
        return super().on_touch_down(touch)


class Tetrivium(App):
    icon = 'data/icon.png'
    local_ip = StringProperty('')
    external_local_ip = StringProperty('')
    remote_ip = StringProperty('')
    port = NumericProperty(0)
    connected = BooleanProperty(False)
    connecting = BooleanProperty(False)
    connect_status = StringProperty('Ready To Connect')
    connect_action = StringProperty('Connect...')
    available_addresses = ListProperty()
    has_crashlog = BooleanProperty(False)
    crashlog_date = StringProperty()
    piece_color2_alpha = NumericProperty(0.333)

    popup = ObjectProperty(allownone=True)
    helppopup = ObjectProperty(allownone=True)

    vibrator = None
    font_file = 'data/4mini.ttf'
    display_border = NumericProperty(16)
    button_scale = NumericProperty(1)
    app_directory = StringProperty()
    shift_pressed = False
    savefolder = StringProperty('histories')
    theme = ObjectProperty()
    infotext = StringProperty()
    infotext_setter = ObjectProperty()

    screen_manager = ObjectProperty()
    game_screen = ObjectProperty()
    replay_screen = ObjectProperty()
    settings_screen = ObjectProperty()
    control_screen = ObjectProperty()
    sprint_screen = ObjectProperty()
    marathon_screen = ObjectProperty()
    multiplayer_screen = ObjectProperty()
    about_screen = ObjectProperty()

    text_scale = NumericProperty(1)
    animations = BooleanProperty(True)
    animation_length = NumericProperty(.2)
    piece_animations = BooleanProperty(True)
    drop_forgive_multiplier = NumericProperty(1)
    clear_length = .5
    fall_length = .15
    background_image = StringProperty('theme/background.png')
    column_image = StringProperty('theme/column.png')
    window_leave_timeout = ObjectProperty(allownone=True)

    rotate_time = NumericProperty(0.33)
    piece_shadow = BooleanProperty(True)
    vibration = BooleanProperty(True)
    play_swipe = BooleanProperty(False)
    play_tap = BooleanProperty(False)
    touch_area = BooleanProperty(False)
    touch_scale = NumericProperty(1)
    touch_rotate = BooleanProperty(True)
    touch_slide = BooleanProperty(True)
    swipe_vertical = BooleanProperty(True)
    deadzone = NumericProperty(0.25)
    sound_effects = BooleanProperty(False)
    volume = NumericProperty(1)
    music_volume = NumericProperty(1)
    pause_data = StringProperty('')
    theme_folder = StringProperty('')
    screen_border = NumericProperty(0)
    line_animations = BooleanProperty(True)

    music_support = BooleanProperty(True)
    music = ObjectProperty(allownone=True)
    music_looper = ObjectProperty(allownone=True)
    music_start_time = 0
    music_pos = 0
    music_loop = NumericProperty(0)
    music_theme = NumericProperty(0)
    musics = ListProperty()
    sounds = DictProperty()
    scores_a = ListProperty()
    scores_b = ListProperty()

    m_left = ListProperty()
    m_right = ListProperty()
    m_down = ListProperty()
    m_rotate_l = ListProperty()
    m_rotate_r = ListProperty()
    m_drop = ListProperty()
    m_store = ListProperty()
    m_pause = ListProperty()

    mp_connection = ObjectProperty(allownone=True)
    mp_ready_start = BooleanProperty(False)
    mp_thinking = BooleanProperty(False)
    multiplayer_text = ListProperty()
    multiplayer_text_current = StringProperty()
    multiplayer_typing = BooleanProperty(False)

    window_maximized = BooleanProperty(False)
    window_top = NumericProperty(0)
    window_left = NumericProperty(0)
    window_width = NumericProperty(400)
    window_height = NumericProperty(600)

    timer_current = 0

    overlay_color = ListProperty([.8, 1, .8, .33])
    selected_object = ObjectProperty(allownone=True)
    last_joystick_axis = NumericProperty(0)

    button_update = BooleanProperty(False)

    def help(self, helptext='Help Text'):
        if self.helppopup:
            return
        content = HelpPopupContent(text=helptext)
        app.helppopup = NormalPopup(title="", content=content, size_hint=(.9, .9), auto_dismiss=False)
        app.helppopup.open()

    def reaction_receive(self, reaction):
        if reaction in emotions_colors.keys():
            reaction_modal = ReactionOverlay(emotion=reaction)
            reaction_modal.open()

    def load_theme(self):
        #This function will handle all theme colors and image loading into local variables.

        default_theme_folder = os.path.join(self.app_directory, 'theme')
        theme_folder = self.get_theme_folder()
        background_test = os.path.join(theme_folder, 'background.png')
        if os.path.isfile(background_test):
            self.background_image = background_test
        else:
            self.background_image = os.path.join(default_theme_folder, 'background.png')

        column_test = os.path.join(theme_folder, 'column.png')
        if os.path.isfile(column_test):
            self.column_image = column_test
        else:
            self.column_image = os.path.join(default_theme_folder, 'column.png')

        default_theme = Theme()
        color_file = 'theme.ini'
        test_file = os.path.join(theme_folder, color_file)
        if os.path.isfile(test_file):
            theme_file = test_file
        else:
            theme_file = os.path.join(default_theme_folder, color_file)
        try:
            config_file = ConfigParser(interpolation=None)
            config_file.read(theme_file)
            sections = config_file.sections()
            try:
                color_alpha = float(config_file.get('Colors', 'color_alpha'))
                self.piece_color2_alpha = color_alpha
            except:
                self.piece_color2_alpha = 0.333
            if 'Colors' in sections:
                for color_name in color_names:
                    try:
                        color_data = config_file.get('Colors', color_name)
                        color_values = color_data.split(',')
                        color_values_float = []
                        for color_value in color_values:
                            color_values_float.append(float(color_value))
                        if len(color_values_float) == len(getattr(self.theme, color_name)):
                            setattr(self.theme, color_name, color_values_float)
                    except Exception as exc:
                        #cant load color, use default color
                        setattr(self.theme, color_name, getattr(default_theme, color_name))
        except:
            #full reset theme
            self.piece_color2_alpha = 0.333
            for color_name in color_names:
                setattr(self.theme, color_name, getattr(default_theme, color_name))
        self.button_update = not self.button_update

    def format_frames(self, frames):
        #Formats a number of frames into a standard minutes:seconds string

        seconds_total = int(round(frames / fps))
        seconds = seconds_total % 60
        minutes = seconds_total // 60
        return str(minutes)+':'+str(seconds).zfill(2)

    def navigation_key(self, key):
        #when given a key code, returns a string value to determine which navigation key was pressed

        if key in navigation_next:
            return 'next'
        elif key in navigation_prev:
            return 'prev'
        elif key in navigation_activate:
            return 'enter'
        elif key in navigation_back:
            return 'back'
        elif key in navigation_left:
            return 'left'
        elif key in navigation_right:
            return 'right'
        else:
            return None

    def dismiss_popup(self, *_):
        #Close the app's open popup if it has one

        if self.popup:
            self.popup.dismiss()
            self.popup = None
            return True
        return False

    def activate_selected(self):
        #Attempts to activate the current selected_object, depending on what kind of widget it is.

        try:
            self.selected_object.trigger_action()
        except:
            pass
        try:
            self.selected_object.focus = True
        except:
            pass

    def find_active(self, root_widget, forward, found):
        if root_widget == self.selected_object and not found:
            #The root widget is the current active! If True is returned when recursively searching, the next recursion level up will try to find the next available widget in the tree
            return True

        if isinstance(root_widget, RecycleView):
            #Recycleview, need to do special stuff to acconut for some children not currently existing
            is_recycle = True
            recycle_layout = root_widget.children[0]
            children = sorted(recycle_layout.children, key=lambda x: (x.y, x.x))
        else:
            #Other types of layouts, just iterate through the child list
            is_recycle = False
            recycle_layout = None
            children = list(root_widget.children)
        if forward:
            children.reverse()

        for index, child in enumerate(children):
            is_selectable = hasattr(child, 'selectable_item') and child.selectable_item
            if found and not child.disabled and is_selectable:
                #last widget in the tree was the old active, now this child becomes the current active
                return child
            found_active = self.find_active(child, forward, found)
            if found_active is True:
                #This child or one of its children is selected, need to find the next possible
                found = True
                if is_recycle and index + 1 >= len(children) and is_selectable:
                    #This recycleview has no more children to switch to, it could be on the last child, or it may need to be scrolled
                    scrollable_x = recycle_layout.width - root_widget.width  #how many pixels of scrolling is available in the x direction
                    scrollable_y = recycle_layout.height - root_widget.height
                    if root_widget.do_scroll_x and scrollable_x > 0:  #root can scroll in horizontal
                        if forward and root_widget.scroll_x > 0:  #root can and should scroll forward
                            root_widget.scroll_x = max(root_widget.scroll_x - (self.selected_object.width / scrollable_x), 0)
                            return self.selected_object
                        elif not forward and root_widget.scroll_x < 1:  #root can and should scroll backward
                            root_widget.scroll_x = min(root_widget.scroll_x + (self.selected_object.width / scrollable_x), 1)
                            return self.selected_object
                    elif root_widget.do_scroll_y and scrollable_y > 0:  #root can scroll in vertical
                        if forward and root_widget.scroll_y > 0:  #root can and should scroll forward
                            root_widget.scroll_y = max(root_widget.scroll_y - (self.selected_object.height / scrollable_y), 0)
                            return self.selected_object
                        elif not forward and root_widget.scroll_y < 1:  #root can and should scroll backward
                            root_widget.scroll_y = min(root_widget.scroll_y + (self.selected_object.height / scrollable_y), 1)
                            return self.selected_object

            elif found_active is None:
                #active not found in this child or its children, move on to the next child
                continue
            else:
                #the next active was found, return it to go up one recursion level
                return found_active

        if found:
            #Tried to find the next active but couldnt, continue search in the next tree up
            return True
        return None  #The active was not found in this tree at all

    def selected_item(self, lookin, forward):
        active = self.find_active(lookin, forward, False)
        if active is True:
            active = self.find_active(lookin, forward, True)
        self.set_current_selected(lookin, active)

    def selected_next(self, lookin):
        #Convenience function for selecting the next widget in the tree
        self.selected_item(lookin, True)

    def selected_prev(self, lookin):
        #Convenience function for selecting the previous widget in the tree
        self.selected_item(lookin, False)

    def set_current_selected(self, lookin, to_select):
        #This function will set a given widget as selected if it is given, otherwise it will find the first valid selectable widget

        if self.selected_object is None and to_select is None:
            for widget in lookin.walk(restrict=True):
                if hasattr(widget, 'selectable_item'):
                    if widget.selectable_item:
                        app.set_selected_overlay(widget)
                        break
        else:
            app.set_selected_overlay(to_select)

    def set_selected_overlay(self, widget):
        #This function will actually set the given widget as the current selected, also ensures it is scrolled to if in a Scroller

        self.selected_object = widget
        if widget is None:
            return
        parent = widget.parent
        while parent is not None:
            if parent.parent == parent:
                break
            if hasattr(parent, 'scroll_y'):
                try:
                    if parent.children[0].height < parent.height:
                        parent.scroll_y = 1
                    else:
                        parent.scroll_to(widget, animate=False, padding=20)
                except:
                    pass
                break
            parent = parent.parent

    def clear_selected_overlay(self, *_):
        #Sets the current selected object to none

        self.selected_object = None

    def timer(self, *_):
        #Testing function, returns the amount of time elapsed since the function was last run

        timer_current = time.time()
        timer_amount = timer_current - self.timer_current
        self.timer_current = timer_current
        return timer_amount

    def load_window_size(self):
        #Loads the window size and position from the settings file, sets it to local variables, and applies the size if necessary

        self.window_maximized = self.config.getboolean('Settings', 'window_maximized')
        if self.window_maximized:
            Window.maximize()
        else:
            self.window_top = int(self.config.get('Settings', 'window_top'))
            self.window_left = int(self.config.get('Settings', 'window_left'))
            self.window_height = int(self.config.get('Settings', 'window_height'))
            self.window_width = int(self.config.get('Settings', 'window_width'))
        if desktop:
            Window.minimum_height = 640
            Window.minimum_width = 480
            if self.window_maximized:
                Window.maximize()
            else:
                Window.size = self.window_width, self.window_height
                Window.left = self.window_left
                Window.top = self.window_top

    def store_window_size(self):
        #Saves the current window size and position to local variables and to the settings file

        self.config.set("Settings", "window_maximized", 1 if self.window_maximized else 0)
        if self.window_maximized:
            return
        self.window_top = Window.top
        self.window_left = Window.left
        self.window_width = Window.size[0]
        self.window_height = Window.size[1]
        self.config.set('Settings', 'window_top', self.window_top)
        self.config.set('Settings', 'window_left', self.window_left)
        self.config.set('Settings', 'window_width', self.window_width)
        self.config.set('Settings', 'window_height', self.window_height)

    def set_scale(self, *_):
        #Sets button and text scale values based on current window size

        self.store_window_size()
        scale = Window.height / 15
        #scale = int(float(cm(0.85)))
        self.display_border = scale / 3
        self.button_scale = scale
        aspect = Window.width / Window.height
        if aspect > 1:
            extra = min(aspect - 1, 0.5)
            self.text_scale = scale / (3.5 - extra)
        else:
            self.text_scale = scale / 4

    def bump(self, level):
        #If the vibrator is activated, vibrates a given strength (level should be 0-5)

        if vibrator:
            if self.vibration:
                vibrate_amounts = [0, .02, .05, .075, .1, .25]
                vibrator.vibrate(vibrate_amounts[level])

    def connection_friendly(self, multiplayer_mode):
        #Returns a 'friendly' formatted string for the current multiplayer mode
        if multiplayer_mode == 'port_forward':
            return 'Port Forwarding'
        elif multiplayer_mode == 'direct':
            return 'Direct Connection'
        elif multiplayer_mode == 'bluetooth':
            return 'Bluetooth Connection'
        else:  #multiplayer_mode == 'local':
            return 'Local'

    def multiplayer_send(self, command, data):
        #sent messages:
        #   'add lines', [number, space]
        #   'game over'
        #   'pause start'
        #   'pause end'
        #   'speed set', [speed]
        #   'filled set', [filled]
        #   'game start', [seed]
        #   'line height', [height]
        #   'leave game'
        #   'chat typing'
        #   'chat not typing'
        #   'chat', [text]
        #   'reaction', [text]
        data = list(map(str, data))
        command = command+';'+','.join(data)
        if self.mp_connection is not None:
            self.mp_connection.send(command)

    def scroll_bottom(self):
        if self.multiplayer_screen:
            self.multiplayer_screen.ids['chatArea'].scroll_y = 0
        if self.game_screen:
            self.game_screen.ids['chatArea'].scroll_y = 0

    def multiplayer_send_message(self):
        if self.multiplayer_text_current:
            self.multiplayer_send('chat', [self.multiplayer_text_current])
            self.multiplayer_text.append({'text': 'Me: '+self.multiplayer_text_current})
            self.scroll_bottom()
            self.multiplayer_text_current = ''

    def multiplayer_receive(self, instance, message):
        command, data = message.split(';', 1)
        multiplayer_screen = self.multiplayer_screen
        if multiplayer_screen is None:
            return
        if command == 'chat typing':
            self.multiplayer_typing = True
        if command == 'chat not typing':
            self.multiplayer_typing = False
        if command == 'chat':
            self.multiplayer_typing = False
            self.multiplayer_text.append({'text': 'Them: '+data})
            self.scroll_bottom()
        data = data.split(',')
        if command == 'speed set':
            multiplayer_screen.other_speed = int(data[0])
        elif command == 'filled set':
            multiplayer_screen.other_filled = int(data[0])
        elif command == 'game start':
            Clock.schedule_once(lambda x: self.multiplayer_screen.start_game_finish(seed=float(data[0])))
            self.multiplayer_send('game ready', [])
        elif command == 'game ready':
            if multiplayer_screen.starting_game:
                Clock.schedule_once(lambda x: multiplayer_screen.start_game_finish())

        game_screen = self.game_screen
        if game_screen is not None:
            if command == 'leave game':
                if self.screen_manager.current == 'game':
                    game_screen.back()
            elif command == 'reaction':
                self.reaction_receive(data[0])
            elif command == 'line height':
                game_screen.opponent_block_height = int(data[0])
            game_running = game_screen.game_running
            if game_running:
                if command == 'add lines':
                    self.play_sound('add_line')
                    lines, spacer = data
                    lines = int(lines)
                    spacer = int(spacer)
                    block = random.randint(0, len(pieces)-1)
                    for index in range(0, lines):
                        game_screen.lines_to_add.append([spacer, block])
                elif command == 'pause start':
                    game_screen.pause(force=True, silent=True)
                elif command == 'pause end':
                    if game_screen.paused:
                        game_screen.pause(silent=True)
                elif command == 'game over':
                    Clock.schedule_once(lambda x: game_screen.game_win())

    def multiplayer_disconnect(self, *_):
        self.multiplayer_text = []
        if self.multiplayer_screen:
            self.multiplayer_screen.starting_game = False
        if self.screen_manager.current == 'game':
            Clock.schedule_once(lambda x: self.game_screen.back())

    def multiplayer_start(self):
        if self.multiplayer_screen is None:
            return
        global socket
        import socket
        global Connector
        from connector import Connector
        if self.mp_connection is None and socket is not None:
            try:
                self.port = int(float(app.config.get('Settings', 'last_multiplayer_port')))
            except:
                self.port = multiplayer_port
            self.mp_connection = Connector(app_name=app_name, port=multiplayer_port)
            self.mp_connection.bind(on_ask_connect=self.multiplayer_screen.ask_connect)
            self.mp_connection.bind(on_connect=self.multiplayer_screen.connected)
            self.mp_connection.bind(on_disconnect=self.multiplayer_disconnect)
            self.mp_connection.bind(on_receive=self.multiplayer_receive)
            self.mp_connection.bind(on_mode=self.multiplayer_screen.stop_game_start)
            self.mp_connection.bind(on_connected=self.save_multiplayer_ip)
            self.mp_connection.bind(on_connected=self.save_port)

            self.mp_connection.bind(local_ip=self.setter('local_ip'))
            self.mp_connection.bind(external_local_ip=self.setter('external_local_ip'))
            self.mp_connection.bind(port=self.setter('port'))
            self.mp_connection.bind(remote_ip=self.setter('remote_ip'))
            self.mp_connection.bind(connected=self.setter('connected'))
            self.mp_connection.bind(connecting=self.setter('connecting'))
            self.mp_connection.bind(connect_status=self.setter('connect_status'))
            self.mp_connection.bind(connect_action=self.setter('connect_action'))
            self.mp_connection.bind(available_addresses=self.setter('available_addresses'))
            self.mp_connection.bind(thinking=self.setter('mp_thinking'))

    def multiplayer_stop(self):
        if self.mp_connection is not None:
            self.mp_connection.stop()

    def save_multiplayer_ip(self, *_):
        if self.mp_connection.mode != 'local':
            self.config.set('Settings', 'last_multiplayer', self.mp_connection.remote_ip)

    def save_port(self, *_):
        if self.mp_connection.mode != 'local':
            self.config.set('Settings', 'last_multiplayer_port', str(self.mp_connection.port))

    def block_file(self, block_type=''):
        if block_type == '':
            return ''
        theme_folder = self.get_theme_folder()
        block_file = 'block-'+block_type.lower()+'.png'
        test_file = os.path.join(theme_folder, block_file)
        if os.path.isfile(test_file):
            return test_file
        else:
            base_file = os.path.join(theme_folder, 'block.png')
            if os.path.isfile(base_file):
                return base_file
            else:
                default_theme_folder = os.path.join(self.app_directory, 'theme')
                original_file = os.path.join(default_theme_folder, block_file)
                return original_file

    def reset_settings(self):
        if desktop:
            touch_area = 0
        else:
            touch_area = 1
        settings = {
                'touch_area': touch_area,
                'touch_scale': 1,
                'vibration': 1,
                'touch_rotate': 1,
                'touch_slide': 1,
                'play_swipe': 0,
                'play_tap': 0,
                'swipe_vertical': 1,
                'rotate_time': 0.25,
                'shadow': 1,
                'deadzone': 0.25,
                'screen_border': 0,
                'theme_folder': '',
                'sound_effects': 1,
                'piece_animations': 1,
                'drop_forgive_multiplier': 1,
                'line_animations': 1,
                'volume': 1,
                'music_volume': 0.5,
                'slected_music': 0,
                'last_multiplayer': '',
                'last_multiplayer_mode': 'local',
                'last_multiplayer_port': '',
                'window_maximized': 0,
                'window_top': 50,
                'window_left': 10,
                'window_width': 400,
                'window_height': 600,
            }
        for setting in settings:
            self.config.set("Settings", setting, settings[setting])
        self.update_config_settings()
        self.load_window_size()

    def build_config(self, config):
        #Setup config file if it is not found
        if desktop:
            touch_area = 0
        else:
            touch_area = 1
        config.setdefaults(
            'Settings', {
                'scores_a': '',
                'scores_b': '',
                'touch_area': touch_area,
                'touch_scale': 1,
                'vibration': 1,
                'touch_rotate': 1,
                'touch_slide': 1,
                'play_swipe': 0,
                'play_tap': 0,
                'swipe_vertical': 1,
                'rotate_time': 0.25,
                'shadow': 1,
                'pause_data': '',
                'deadzone': 0.25,
                'screen_border': 0,
                'theme_folder': '',
                'sound_effects': 1,
                'piece_animations': 1,
                'drop_forgive_multiplier': 1,
                'line_animations': 1,
                'volume': 1,
                'music_volume': 0.5,
                'slected_music': 0,
                'last_multiplayer': '',
                'last_multiplayer_mode': 'local',
                'last_multiplayer_port': '',
                'window_maximized': 0,
                'window_top': 50,
                'window_left': 10,
                'window_width': 400,
                'window_height': 600,
            })
        config.setdefaults(
            'Controls', {
                'm_left': ','.join([str(item) for item in default_c_left]),
                'm_right': ','.join([str(item) for item in default_c_right]),
                'm_rotate_l': ','.join([str(item) for item in default_c_rotate_l]),
                'm_rotate_r': ','.join([str(item) for item in default_c_rotate_r]),
                'm_down': ','.join([str(item) for item in default_c_down]),
                'm_drop': ','.join([str(item) for item in default_c_drop]),
                'm_store': ','.join([str(item) for item in default_c_store]),
                'm_pause': ','.join([str(item) for item in default_c_pause]),
            })

    def on_config_change(self, config, section, key, value):
        self.update_config_settings()

    def update_config_settings(self, *_):
        self.theme_folder = self.config.get("Settings", "theme_folder")
        self.piece_shadow = self.config.getboolean("Settings", "shadow")
        self.vibration = self.config.getboolean("Settings", "vibration")
        self.touch_area = self.config.getboolean("Settings", "touch_area")
        self.touch_scale = float(self.config.get("Settings", "touch_scale"))
        self.touch_rotate = self.config.getboolean("Settings", "touch_rotate")
        self.touch_slide = self.config.getboolean("Settings", "touch_slide")
        self.play_swipe = self.config.getboolean("Settings", "play_swipe")
        self.play_tap = self.config.getboolean("Settings", "play_tap")
        self.rotate_time = float(self.config.get("Settings", "rotate_time"))
        self.swipe_vertical = self.config.getboolean("Settings", "swipe_vertical")
        self.deadzone = float(self.config.get("Settings", "deadzone"))
        self.sound_effects = self.config.getboolean("Settings", "sound_effects")
        self.volume = float(self.config.get("Settings", "volume"))
        self.music_volume = float(self.config.get('Settings', 'music_volume'))
        self.music_theme = int(self.config.get('Settings', 'slected_music'))
        self.piece_animations = self.config.getboolean("Settings", "piece_animations")
        self.drop_forgive_multiplier = float(self.config.get('Settings', 'drop_forgive_multiplier'))
        self.line_animations = self.config.getboolean("Settings", "line_animations")
        self.screen_border = int(self.config.get("Settings", "screen_border"))

    def message(self, text, timeout=20):
        """Sets the app.infotext variable to a specific message, and clears it after a set amount of time."""

        self.infotext = text
        if self.infotext_setter:
            self.infotext_setter.cancel()
        self.infotext_setter = Clock.schedule_once(self.clear_message, timeout)

    def clear_message(self, *_):
        self.infotext = ''

    def load_scores(self):
        self.scores_a = self.load_score('scores_a')
        self.scores_b = self.load_score('scores_b')

    def load_score(self, score_name):
        scores_data = self.config.get("Settings", score_name).split(';')
        scores = []
        for score in scores_data:
            try:
                score_value, score_lines, score_date = score.split(',', 2)
                score_value = int(score_value)
                score_lines = int(score_lines)
                scores.append([score_value, score_lines, score_date])
            except:
                pass
        return scores

    def clear_scores(self):
        self.scores_a = []
        self.scores_b = []
        self.save_scores()

    def add_score(self, score, lines, date_data, mode):
        self.load_scores()
        if mode == 'C':
            return
        elif mode == 'B':
            self.scores_b.append([score, lines, date_data])
        else:
            self.scores_a.append([score, lines, date_data])
        self.sort_scores()
        self.save_scores()

    def sort_scores(self):
        self.scores_a = sorted(self.scores_a, key=lambda x: x[0], reverse=True)[:10]
        self.scores_b = sorted(self.scores_b, key=lambda x: x[0] / (x[1] + 1), reverse=True)[:10]

    def save_scores(self):
        self.save_score(self.scores_a, 'scores_a')
        self.save_score(self.scores_b, 'scores_b')
        self.config.write()

    def save_score(self, score_data, settings_string):
        all_score_data = ''
        for score in score_data:
            score_data = str(score[0])+','+str(score[1])+','+score[2]
            if all_score_data:
                all_score_data = all_score_data+';'
            all_score_data = all_score_data+score_data
        self.config.set("Settings", settings_string, all_score_data)

    def parse_controls(self, control_name):
        controls_numbers = []
        controls = self.config.get("Controls", control_name)
        controls_list = controls.split(',')
        for control in controls_list:
            try:
                control_number = int(control)
                controls_numbers.append(control_number)
            except:
                pass
        return controls_numbers

    def unparse_controls(self, controls):
        controls_list = []
        for control in controls:
            controls_list.append(str(control))
        return ','.join(controls_list)

    def load_keys(self):
        self.m_left = self.parse_controls("m_left")
        self.m_right = self.parse_controls("m_right")
        self.m_down = self.parse_controls("m_down")
        self.m_rotate_l = self.parse_controls("m_rotate_l")
        self.m_rotate_r = self.parse_controls("m_rotate_r")
        self.m_drop = self.parse_controls("m_drop")
        self.m_store = self.parse_controls("m_store")
        self.m_pause = self.parse_controls("m_pause")

    def load_sound(self, sound_name, default=False):
        if default:
            theme_folder = os.path.join(self.app_directory, 'theme')
        else:
            theme_folder = self.get_theme_folder()
        sound_filename = os.path.join(theme_folder, sound_name+'.wav')
        sound = None
        if resource_find(sound_filename):
            #sound = SoundFXLoader.load(sound_filename)
            sound = SoundFX(source=resource_find(sound_filename))
            sound.load()
        return sound

    def on_sound_effects(self, *_):
        if self.sound_effects is True:
            self.load_sounds()

    def load_sounds(self, default=False):
        loaded_sounds = 0
        self.sounds = {}
        sound_names = [['rotate', 3], ['rotate_fail', 2], ['button', 1], ['fall', 1], ['lock', 1], ['line', 1], ['max_lines', 1], ['line_fall', 1], ['wall', 1], ['move', 1], ['store', 1], ['level', 1], ['new_game', 1], ['game_over', 1], ['pause', 1], ['game_win', 1], ['add_line', 2]]
        for sound_data in sound_names:
            sound_name = sound_data[0]
            self.sounds[sound_name] = []
            if self.sound_effects:
                for index in range(sound_data[1]):
                    sound_data = self.load_sound(sound_name, default=default)
                    if sound_data is not None:
                        loaded_sounds += 1
                    self.sounds[sound_name].append(sound_data)
            else:
                self.sounds[sound_name].append(None)
        if self.sound_effects and not default and loaded_sounds == 0:
            #No sounds were loaded when they should be, load defaults instead
            self.load_sounds(default=True)
        elif default:
            #no sounds found, treat folder as a music directory instead
            self.load_musics(extra=True)
        else:
            self.load_musics()

    def load_musics(self, extra=False):
        music_data = []
        exts = ['.ogg', '.mp3', '.wav']
        theme_folder_root = self.get_theme_folder()
        theme_folder = os.path.join(theme_folder_root, 'music')
        if not os.path.isdir(theme_folder):
            theme_folder = theme_folder_root
        if os.path.isdir(theme_folder):
            for file in os.listdir(theme_folder):
                if os.path.splitext(file)[1] in exts:
                    #music found, look for music settings file
                    settings_file = os.path.splitext(file)[0]+'.txt'
                    try:
                        settings_filepath = os.path.join(theme_folder, settings_file)
                        music_settings_file = open(settings_filepath, 'r')
                        music_settings = music_settings_file.readlines()
                        music_settings_file.close()
                        loop_offset = float(music_settings[0])
                    except Exception as e:
                        loop_offset = 0
                    music_file = os.path.join(theme_folder, file)
                    music_data.append([file, music_file, loop_offset])
        music_data = sorted(music_data, key=lambda x: x[0])
        self.musics = [['', '', 0]] + music_data

    def clear_replays(self):
        if self.popup:
            return
        content = ConfirmPopupContent(text="This will permanently delete all replays", yes_text='Delete', no_text="Don't Delete")
        content.bind(on_answer=self.clear_replays_answer)
        self.popup = NormalPopup(title="Delete All Replays?", content=content, size_hint=(1, None), size=(1000, self.button_scale * 3), auto_dismiss=False)
        self.popup.bind(on_dismiss=self.dismiss_popup)
        self.popup.open()

    def clear_replays_answer(self, instance, answer):
        self.dismiss_popup()
        if answer == 'yes':
            histories_folder = os.path.join(self.savefolder, 'histories')
            files = reversed(os.listdir(histories_folder))
            for file in files:
                filename, extension = os.path.splitext(file)
                if extension.lower() == '.txt':
                    history_path = os.path.join(histories_folder, file)
                    try:
                        os.remove(history_path)
                    except:
                        pass
            self.replay_screen.update_histories()

    def on_start(self):
        self.load_keys()
        keys_not_set = self.keys_not_set()
        if keys_not_set:
            self.show_settings()
            self.message("Warning: controls are not set")
        if platform == 'android':
            from android.permissions import request_permission, check_permission, Permission
            can_write_external = check_permission(Permission.WRITE_EXTERNAL_STORAGE)
            if not can_write_external:
                request_permission(Permission.WRITE_EXTERNAL_STORAGE)
            can_vibrate = check_permission(Permission.VIBRATE)
            if not can_vibrate:
                request_permission(Permission.VIBRATE)
            can_internet = check_permission(Permission.INTERNET)
            if not can_internet:
                request_permission(Permission.INTERNET)
            #request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.VIBRATE, Permission.INTERNET])

            can_vibrate = check_permission(Permission.VIBRATE)
            if not can_vibrate:
                global vibrator
                vibrator = None
        Logger.info("Startup Time: "+str(time.time() - startup_time))

    def keys_not_set(self):
        not_set = []
        if not self.m_left:
            not_set.append('m_left')
        if not self.m_right:
            not_set.append('m_right')
        if not self.m_down:
            not_set.append('m_down')
        if not self.m_rotate_l:
            not_set.append('m_rotate_l')
        if not self.m_rotate_r:
            not_set.append('m_rotate_r')
        if not self.m_drop:
            not_set.append('m_drop')
        if not self.m_store:
            not_set.append('m_store')
        return not_set

    def on_pause(self):
        if self.screen_manager.current == 'game':
            self.game_screen.pause(True)
            self.game_screen.save_pause()
        self.save_config()
        return True

    def on_stop(self):
        self.multiplayer_stop()
        if self.screen_manager.current == 'game':
            self.game_screen.pause(True)
            self.game_screen.save_pause()
        self.save_config()

    def store_pause(self):
        pause_data = self.pause_data
        self.config.set("Settings", "pause_data", pause_data)

    def save_controls(self):
        self.config.set("Controls", "m_left", self.unparse_controls(self.m_left))
        self.config.set("Controls", "m_right", self.unparse_controls(self.m_right))
        self.config.set("Controls", "m_rotate_l", self.unparse_controls(self.m_rotate_l))
        self.config.set("Controls", "m_rotate_r", self.unparse_controls(self.m_rotate_r))
        self.config.set("Controls", "m_down", self.unparse_controls(self.m_down))
        self.config.set("Controls", "m_drop", self.unparse_controls(self.m_drop))
        self.config.set("Controls", "m_store", self.unparse_controls(self.m_store))
        self.config.set("Controls", "m_pause", self.unparse_controls(self.m_pause))

    def save_config(self):
        self.store_pause()
        self.config.set("Settings", "shadow", 1 if self.piece_shadow else 0)
        self.config.set("Settings", "vibration", 1 if self.vibration else 0)
        self.config.set("Settings", "touch_area", 1 if self.touch_area else 0)
        self.config.set("Settings", "touch_scale", self.touch_scale)
        self.config.set("Settings", "touch_rotate", 1 if self.touch_rotate else 0)
        self.config.set("Settings", "touch_slide", 1 if self.touch_slide else 0)
        self.config.set("Settings", "rotate_time", self.rotate_time)
        self.config.set("Settings", "sound_effects", 1 if self.sound_effects else 0)
        self.config.set("Settings", "play_swipe", 1 if self.play_swipe else 0)
        self.config.set("Settings", "play_tap", 1 if self.play_tap else 0)
        self.config.set("Settings", "volume", self.volume)
        self.config.set("Settings", "music_volume", self.music_volume)
        self.config.set("Settings", "slected_music", self.music_theme)
        self.config.set("Settings", "theme_folder", self.theme_folder)
        self.config.set("Settings", "piece_animations", 1 if self.piece_animations else 0)
        self.config.set("Settings", "drop_forgive_multiplier", self.drop_forgive_multiplier)
        self.config.set("Settings", "line_animations", 1 if self.line_animations else 0)
        self.config.set("Settings", "screen_border", self.screen_border)
        self.config.set("Settings", "deadzone", self.deadzone)
        self.config.set("Settings", "swipe_vertical", 1 if self.swipe_vertical else 0)
        self.save_controls()
        self.save_scores()

    def get_theme_folder(self):
        self.on_theme_folder()
        if not self.theme_folder:
            theme_folder = os.path.join(self.app_directory, 'theme')
            return theme_folder
        else:
            return self.theme_folder

    def on_theme_folder(self, *_):
        if not os.path.isdir(self.theme_folder):
            self.theme_folder = ''

    def get_application_config(self, **kwargs):
        self.app_directory = app_directory
        Logger.info('App Folder: '+self.app_directory)

        savefolder, config_file = get_config_file()

        Logger.info("Config File: "+config_file)
        return config_file

    def build(self):
        global app
        app = self
        savefolder_loc, config_file_loc = get_config_file()
        self.savefolder = savefolder_loc
        crashlog = get_crashlog()
        if os.path.isfile(crashlog):
            self.has_crashlog = True
            crashlog_timestamp = os.path.getmtime(crashlog)
            self.crashlog_date = datetime.fromtimestamp(crashlog_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        else:
            self.has_crashlog = False
        if vibrator:
            self.vibrator = True
        else:
            self.vibrator = False
        self.mp_connection = None
        history_folder = os.path.join(self.savefolder, 'histories')
        if not os.path.isdir(history_folder):
            os.makedirs(history_folder)
        self.update_config_settings()
        self.on_theme_folder()
        self.theme = Theme()
        self.load_theme()
        self.load_scores()
        self.sort_scores()
        self.pause_data = self.config.get("Settings", "pause_data")
        #self.load_sounds()
        self.load_window_size()
        self.set_scale()
        Window.bind(on_maximize=self.set_maximized)
        Window.bind(on_restore=self.unset_maximized)
        Window.bind(on_draw=self.set_scale)
        Window.bind(on_cursor_leave=self.window_exited)
        Window.bind(on_cursor_enter=self.window_entered)
        Window.bind(on_key_down=self.key_down)
        Window.bind(on_key_up=self.key_up)
        Window.bind(on_joy_button_down=self.joy_down)
        Window.bind(on_joy_button_up=self.joy_up)
        Window.bind(on_joy_axis=self.joy_axis)
        Window.bind(on_joy_hat=self.joy_hat)
        EventLoop.window.bind(on_keyboard=self.hook_keyboard)
        self.screen_manager = MainScreenManager()
        self.screen_manager.transition = SlideTransition()
        self.screen_manager.add_widget(MainScreen(name='main'))
        return self.screen_manager

    def set_maximized(self, *_):
        self.window_maximized = True

    def unset_maximized(self, *_):
        self.window_maximized = False

    def window_exited(self, window):
        if desktop:
            self.window_leave_timeout = Clock.schedule_once(self.pause_game, .5)

    def window_entered(self, window):
        if desktop:
            if self.window_leave_timeout is not None:
                self.window_leave_timeout.cancel()
                self.window_leave_timeout = None

    def pause_game(self, *_):
        if self.game_screen is not None:
            if not self.game_screen.replay:
                if self.game_screen.game_mode != 'C':
                    self.game_screen.pause(force=True)

    def main(self, direction='right'):
        keys_not_set = self.keys_not_set()
        if keys_not_set:
            self.show_settings()
            self.message("Warning: controls are not set")
        else:
            self.screen_manager.transition.direction = direction
            self.screen_manager.current = 'main'

    def resume_game(self):
        self.game()
        self.game_screen.resume_pause()

    def start_game(self):
        self.game()
        self.game_screen.game_mode = 'A'
        self.game_screen.start_game()

    def game(self, direction='left'):
        from gamescreen import GameScreen
        if self.game_screen is None:
            self.game_screen = GameScreen(name='game')
            self.screen_manager.add_widget(self.game_screen)
        self.screen_manager.transition.direction = direction
        self.screen_manager.current = 'game'

    def replay(self, direction='left'):
        if self.replay_screen is None:
            from replayscreen import ReplayScreen
            self.replay_screen = ReplayScreen(name='replay')
            self.screen_manager.add_widget(self.replay_screen)
        self.screen_manager.transition.direction = direction
        self.screen_manager.current = 'replay'

    def show_settings(self, screen=''):
        if self.settings_screen is None:
            from settingsscreen import SettingsScreen
            self.settings_screen = SettingsScreen(name='settings')
            self.screen_manager.add_widget(self.settings_screen)
        self.settings_screen.from_screen = screen
        self.screen_manager.transition.direction = 'up'
        self.screen_manager.current = 'settings'

    def control_settings(self, control):
        if self.control_screen is None:
            from settingsscreen import ControlScreen
            self.control_screen = ControlScreen(name='control')
            self.screen_manager.add_widget(self.control_screen)
        self.control_screen.control = control
        self.screen_manager.transition.direction = 'up'
        self.screen_manager.current = 'control'

    def sprint(self, direction='left'):
        if self.sprint_screen is None:
            from startscreens import SprintScreen
            self.sprint_screen = SprintScreen(name='sprint')
            self.screen_manager.add_widget(self.sprint_screen)
        self.screen_manager.transition.direction = direction
        self.screen_manager.current = 'sprint'

    def marathon(self, direction='left'):
        if self.marathon_screen is None:
            from startscreens import MarathonScreen
            self.marathon_screen = MarathonScreen(name='marathon')
            self.screen_manager.add_widget(self.marathon_screen)
        self.screen_manager.transition.direction = direction
        self.screen_manager.current = 'marathon'

    def multiplayer(self, direction='left'):
        if self.multiplayer_screen is None:
            from startmultiplayerscreen import MultiplayerScreen
            self.multiplayer_screen = MultiplayerScreen(name='multiplayer')
            self.screen_manager.add_widget(self.multiplayer_screen)
        self.screen_manager.transition.direction = direction
        self.screen_manager.current = 'multiplayer'

    def about(self):
        if self.about_screen is None:
            from settingsscreen import AboutScreen
            self.about_screen = AboutScreen(name='about')
            self.screen_manager.add_widget(self.about_screen)
        self.screen_manager.transition.direction = 'up'
        self.screen_manager.current = 'about'

    def replay_file(self, filepath):
        self.game()
        self.game_screen.replay_path = filepath
        self.game_screen.replay = True
        self.game_screen.start_game(playback=True)

    def hook_keyboard(self, window, scancode, *_):
        """This function receives keyboard events"""

        if scancode == 27:
            if self.helppopup:
                self.helppopup.dismiss()
                self.helppopup = None
                return True
            current_screen = self.screen_manager.current_screen
            dismiss = current_screen.dismiss()
            if dismiss:
                return True
            else:
                if self.screen_manager.current != 'main':
                    self.screen_manager.current_screen.back()
                    return True
        return False

    def joy_down(self, window, padindex, button):
        self.key_down(window, scancode=(0 - button))

    def joy_up(self, window, padindex, button):
        self.key_up(window, scancode=(0 - button))

    def joy_axis(self, window, stickid, axisid, axis):
        axis = axis / 32768
        if axis == 0:
            self.last_joystick_axis = 0
        current_time = time.time()
        if current_time - self.last_joystick_axis > 1:
            if axisid == 0:
                if axis < (0 - self.deadzone):
                    self.key_down(window, scancode=276)
                    self.last_joystick_axis = current_time
                elif axis > self.deadzone:
                    self.key_down(window, scancode=275)
                    self.last_joystick_axis = current_time
                else:
                    self.key_up(window, scancode=276)
                    self.key_up(window, scancode=275)
            elif axisid == 1:
                if axis < (0 - self.deadzone):
                    self.key_down(window, scancode=273)
                    self.last_joystick_axis = current_time
                elif axis > self.deadzone:
                    self.key_down(window, scancode=274)
                    self.last_joystick_axis = current_time
                else:
                    self.key_up(window, scancode=273)
                    self.key_up(window, scancode=274)

    def joy_hat(self, window, stickid, axisid, axis):
        axis_x, axis_y = axis

        if axis_x < 0:
            self.key_down(window, scancode=276)
        elif axis_x > 0:
            self.key_down(window, scancode=275)
        elif axis_x == 0:
            self.key_up(window, scancode=276)
            self.key_up(window, scancode=275)
        if axis_y > 0:
            self.key_down(window, scancode=273)
        elif axis_y < 0:
            self.key_down(window, scancode=274)
        elif axis_x == 0:
            self.key_up(window, scancode=273)
            self.key_up(window, scancode=274)

    def key_down(self, window, scancode=None, *_):
        """Intercepts various key presses and sends commands to the current screen."""
        #print(scancode)
        if scancode == 27:
            return
        if self.popup:
            self.popup.key(scancode, down=True)
        else:
            current_screen = self.screen_manager.current_screen
            current_screen.key(scancode, down=True)

    def key_up(self, window, scancode=None, *_):
        if scancode == 27:
            return
        if self.popup:
            self.popup.key(scancode, down=False)
        else:
            current_screen = self.screen_manager.current_screen
            current_screen.key(scancode, down=False)

    def play_sound(self, action):
        #possible action values:
        #   button - button click (menus)
        #   fall - piece hits floor
        #   lock - piece locks in place after hitting
        #   line - line completed
        #   max_lines - 4 lines completed
        #   wall - piece hits wall
        #   move - piece moves left/right
        #   rotate - piece is rotated
        #   rotate_fail - piece cannot rotate
        #   store - piece is stored/recalled
        #   level - level up
        #
        #   new_game - played at the start of a game
        #   game_win - played when a mode b game is won
        #   game_over - played when game ends
        #   pause - played when game is paused
        #
        #   add_line - multiplayer added a line

        if action in ['wall', 'fall', 'rotate_fail']:
            self.bump(2)
        elif action == 'lock':
            self.bump(3)
        elif action in ['line', 'max_lines']:
            self.bump(3)
        elif action == 'add_line':
            self.bump(4)
        elif action in ['move', 'rotate', 'button']:
            self.bump(1)

        length = 0
        if self.sound_effects:
            sound = self.sounds[action].pop(0)
            if sound:
                sound.volume = self.volume
                sound.play()
                length = sound.length
            self.sounds[action].append(sound)
        return length

    def start_music(self, *_):
        if self.music:
            self.stop_music()
        if self.music_support and self.musics:
            if len(self.musics) - 1 >= self.music_theme:
                music_data = self.musics[self.music_theme]
                music_file, music_filename, loop_point = music_data
                if music_filename:
                    if resource_find(music_filename):
                        music_ext = os.path.splitext(music_filename)[1]
                        self.music_loop = loop_point
                        if music_ext == '.ogg':
                            pass
                        self.music = SoundMusic(source=music_filename)
                        self.music.load()

    def pause_music(self):
        self.cancel_loop()
        if self.music:
            self.music_pos = time.time() - self.music_start_time
            self.music.stop()

    def resume_music(self):
        self.cancel_loop()
        if self.music:
            self.music_start_time = time.time()
            self.music.volume = self.music_volume

            self.music.play()
            if self.music_loop > 0:
                self.music_looper = Clock.schedule_once(self.loop_music, self.music_loop)
            else:
                self.music.loop = True

    def loop_music(self, *_):
        if self.music:
            self.music.stop()
            self.music.play()
            self.music_looper = Clock.schedule_once(self.loop_music, self.music_loop)

    def cancel_loop(self):
        if self.music_looper is not None:
            try:
                self.music_looper.cancel()
            except:
                pass
            self.music_looper = None

    def stop_music(self):
        self.cancel_loop()
        if self.music:
            self.music.stop()
            self.music = None


if __name__ == '__main__':
    try:
        Tetrivium().run()
    except Exception as e:
        try:
            save_crashlog()
        except:
            pass
