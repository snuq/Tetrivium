import re
import time
import random
import os
from kivy.uix.widget import Widget
from kivy.app import App
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.properties import AliasProperty, ObjectProperty, StringProperty, ListProperty, BooleanProperty, NumericProperty, DictProperty
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stencilview import StencilView
from kivy.uix.dropdown import DropDown
from kivy.uix.screenmanager import Screen
from kivy.uix.modalview import ModalView
from kivy.uix.behaviors import ButtonBehavior
from kivy.logger import Logger, LoggerHistory
from kivy.lang.builder import Builder
from globals import emotions_colors
Builder.load_string("""
<ReactionButton>:
    allow_stretch: True
    source: 'data/faces/'+self.emotion+'.png' if self.emotion else ''

<-ReactionOverlay>:
    canvas:
        Color:
            rgba: root.color[0], root.color[1], root.color[2], root.image_opacity
        Rectangle:
            size: app.button_scale, app.button_scale
            pos: root.image_x * root.width, root.image_y * root.height
            source: 'data/faces/'+root.emotion+'.png'
    auto_dismiss: False

<Spacer>:
    canvas:
        Color:
            rgba: app.theme.button_text
        Rectangle:
            pos: self.pos[0], self.pos[1] + (self.height / 2) - 2
            size: self.width, 4
    size_hint: 1, None
    height: app.button_scale / 2

<-FillImage>:

<FastForwardLabel>:
    opacity: 0
    size_hint_y: None
    height: app.button_scale
    pos: 0, self.parent.height - self.height
    font_size: app.text_scale * 2
    text: 'Fast Forward'

<LayoutSplitter>:
    size_hint_y: None
    wider: True if self.owner.width > self.owner.height else False
    cols: 2 if self.wider else 1
    height: self.minimum_height

<ScreenLayout>:
    canvas:
        Color:
            rgba: app.theme.background_overlay
        Rectangle:
            texture: self.texture
            size: self.norm_image_size
            pos: self.center_x - self.norm_image_size[0] / 2., self.center_y - self.norm_image_size[1] / 2.
    source: app.background_image

<TetraScreen>:
    canvas.before:
        Color:
            rgba: app.theme.background
        Rectangle:
            pos: self.pos
            size: self.size

<Countdown>:
    canvas.before:
        Color:
            rgba: root.bg_color
        Rectangle:
            size: self.size
            pos: self.pos
    orientation: 'vertical'
    Widget:
    NormalLabel:
        color: 1, 1, 1, 1
        font_size: 100
        text: str(root.countdown)
    Widget:

<StencilBox>:

<Scroller>:
    scroll_distance: 10
    scroll_timeout: 100
    bar_width: int(app.button_scale * .5)
    bar_color: app.theme.scroller_selected
    bar_inactive_color: app.theme.scroller
    scroll_type: ['bars', 'content']

<NormalRecycleView>:
    size_hint: 1, 1
    do_scroll_x: False
    do_scroll_y: True
    scroll_distance: 10
    scroll_timeout: 200
    bar_width: int(app.button_scale * .5)
    bar_color: app.theme.scroller_selected
    bar_inactive_color: app.theme.scroller
    scroll_type: ['bars', 'content']

<Header@BoxLayout>:
    canvas.before:
        Color:
            rgba: app.theme.header_background
        Rectangle:
            size: self.size[0], self.size[1] + 4
            pos: self.pos[0], self.pos[1] - 4
            source: 'data/header.png'
    size_hint_y: None
    height: app.button_scale
    orientation: 'horizontal'

<NormalLabel>:
    mipmap: True
    color: app.theme.text
    font_size: app.text_scale
    font_name: app.font_file

<LeftNormalLabel>:
    shorten: True
    shorten_from: 'right'
    font_size: app.text_scale
    size_hint_x: 1
    text_size: self.size
    halign: 'left'
    valign: 'middle'

<ChatLabel>:
    font_size: app.text_scale
    padding: 0, app.button_scale / 10
    message_id: -1
    orientation: 'vertical'
    size_hint: 1, None
    height: self.texture_size[1]
    text_size: self.width, None
    size: self.texture_size

<ShortLabel>:
    mipmap: True
    shorten: True
    shorten_from: 'right'
    font_size: app.text_scale
    size_hint_x: 1
    size_hint_max_x: self.texture_size[0]

<InfoLabel>:
    canvas.before:
        Color:
            rgba: root.bgcolor
        Rectangle:
            pos: self.pos
            size: self.size
    mipmap: True
    size_hint_x: None
    width: self.texture_size[0]
    text: app.infotext
    color: app.theme.info_text

<HeaderLabel@Label>:
    mipmap: True
    color: app.theme.header_text
    font_size: int(app.text_scale * 1.5)
    font_name: app.font_file
    bold: True

<MultilineLabel@Label>:
    mipmap: True
    color: app.theme.text
    font_size: app.text_scale
    size_hint_y: None
    multiline: True
    text_size: self.width, None
    size: self.texture_size

<NormalPopup>:
    overlay_color: app.theme.background
    background_color: app.theme.background
    background: 'data/transparent.png'
    separator_color: 1, 1, 1, .25
    title_size: app.text_scale * 1.25
    title_color: app.theme.header_text
    title_font: app.font_file

<HelpPopupContent>:
    cols:1
    RelativeLayout:
        Scroller:
            size_hint: 1, 1
            do_scroll_y: True
            do_scroll_x: False
            BoxLayout:
                size_hint_y: None
                height: self.minimum_height
                orientation: 'vertical'
                id: textArea
        Button:
            size_hint: 1, 1
            opacity: 0
            on_release: root.close()
    GridLayout:
        cols:1
        size_hint_y: None
        height: app.button_scale
        WideButton:
            id: button
            text: 'Close'
            on_release: root.close()

<ConfirmPopupContent>:
    orientation: 'vertical'
    NormalLabel:
        text: root.text
    Label:
    GridLayout:
        cols: 2
        size_hint_y: None
        height: app.button_scale
        WideButton:
            text: root.yes_text
            on_release: root.dispatch('on_answer','yes')
        WideButton:
            text: root.no_text
            on_release: root.dispatch('on_answer', 'no')

<-Slider>:

<NormalSlider>:
    #:set sizing 18
    canvas:
        Color:
            rgba: app.theme.slider_background
        BorderImage:
            border: (0, 0, 0, 0)
            pos: self.pos
            size: self.size
            source: 'data/sliderbg.png'
        Color:
            rgba: app.theme.slider_grabber
        Rectangle:
            pos: (self.value_pos[0] - self.height/4, self.center_y - self.height/2)
            size: self.height/2, self.height
            source: 'data/buttonflat.png'
    canvas.after:
        Color:
            rgba: app.overlay_color if app.selected_object == self else (1, 1, 1, 0)
        Rectangle:
            size: self.size
            pos: self.pos
    min: -1
    max: 1
    value: 0

<-TextInput>:
    canvas.before:
        Color:
            rgba: self.background_color
        BorderImage:
            display_border: [app.display_border/2, app.display_border/2, app.display_border/2, app.display_border/2]
            border: self.border
            pos: self.pos[0] + 3, self.pos[1] + 3
            size: self.size[0] -6, self.size[1] - 6
            source: self.background_active if self.focus else (self.background_disabled_normal if self.disabled else self.background_normal)
        Color:
            rgba:
                (self.cursor_color
                if self.focus and not self._cursor_blink
                else (0, 0, 0, 0))
        Rectangle:
            pos: self._cursor_visual_pos
            size: root.cursor_width, -self._cursor_visual_height
        Color:
            rgba: self.disabled_foreground_color if self.disabled else (self.hint_text_color if not self.text else self.foreground_color)
    canvas.after:
        Color:
            rgba: app.overlay_color if app.selected_object == self else (1, 1, 1, 0)
        Rectangle:
            size: self.size
            pos: self.pos
    font_name: app.font_file

<NormalInput>:
    padding: app.button_scale/4
    mipmap: True
    cursor_color: app.theme.text
    write_tab: False
    background_color: app.theme.input_background
    hint_text_color: app.theme.disabled_text
    disabled_foreground_color: 1,1,1,.75
    foreground_color: app.theme.text
    font_size: app.text_scale

<FloatInput>:
    padding: app.button_scale/4
    write_tab: False
    background_color: app.theme.input_background
    disabled_foreground_color: 1,1,1,.75
    foreground_color: app.theme.text
    font_size: app.text_scale

<IntegerInput>:
    padding: app.button_scale/4
    write_tab: False
    background_color: app.theme.input_background
    disabled_foreground_color: 1,1,1,.75
    foreground_color: app.theme.text
    font_size: app.text_scale

<IPInput>:
    padding: app.button_scale/4
    write_tab: False
    background_color: app.theme.input_background
    disabled_foreground_color: 1,1,1,.75
    foreground_color: app.theme.text
    font_size: app.text_scale

<-Button,-ToggleButton>:
    state_image: self.background_normal if self.state == 'normal' else self.background_down
    disabled_image: self.background_disabled_normal if self.state == 'normal' else self.background_disabled_down
    canvas:
        Color:
            rgba: self.background_color
        BorderImage:
            display_border: [app.display_border, app.display_border, app.display_border, app.display_border]
            border: self.border
            pos: self.pos
            size: self.size
            source: self.disabled_image if self.disabled else self.state_image
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            texture: self.texture
            size: self.texture_size
            pos: int(self.center_x - self.texture_size[0] / 2.), int(self.center_y - self.texture_size[1] / 2.)

<ButtonBase>:
    mipmap: True
    background_normal: 'data/button.png'
    background_down: self.background_normal
    background_disabled_down: self.background_normal
    background_disabled_normal: self.background_normal
    on_press: app.play_sound('button')
    shorten: True
    shorten_from: 'right'
    font_name: app.font_file
    button_update: app.button_update
    canvas.after:
        Color:
            rgba: app.overlay_color if app.selected_object == self else (1, 1, 1, 0)
        Rectangle:
            size: self.size
            pos: self.pos

<NormalButton>:
    width: self.texture_size[0] + app.text_scale * 2
    size_hint_x: None
    font_size: app.text_scale

<WideButton>:
    font_size: app.text_scale
    text_size: self.size
    halign: 'center'
    valign: 'middle'

<ToggleBase>:
    canvas.after:
        Color:
            rgba: app.overlay_color if app.selected_object == self else (1, 1, 1, 0)
        Rectangle:
            size: self.size
            pos: self.pos
    button_update: app.button_update

<NormalToggle@ToggleBase>:
    always_release: True
    toggle: True
    font_size: app.text_scale
    size_hint_x: None
    width: self.texture_size[0] + 20

<WideToggle@ToggleBase>:
    always_release: True
    toggle: True
    font_size: app.text_scale
    size_hint_x: 1

<MenuButton>:
    size_hint_y: None
    height: app.button_scale
    menu: True
    size_hint_x: 1

<NormalMenuStarter@ButtonBase>:
    canvas.after:
        Color:
            rgba: self.color
        Rectangle:
            pos: (root.pos[0]+root.width-(root.height/1.5)), root.pos[1]
            size: root.height/2, root.height
            source: 'data/menuarrows.png'
    menu: True
    size_hint_x: None
    width: self.texture_size[0] + (app.button_scale * 1.5)

<WideMenuStarter@ButtonBase>:
    canvas.after:
        Color:
            rgba: self.color
        Rectangle:
            pos: (root.pos[0]+root.width-(root.height/1.5)), root.pos[1]
            size: root.height/2, root.height
            source: 'data/menuarrows.png'
    menu: True
    text_size: self.size
    halign: 'center'
    valign: 'middle'
    size_hint_x: 1

<IndexToggle>:
    size_hint_y: None
    height: app.button_scale
    always_release: True
    toggle: True
    font_size: app.text_scale

<SettingsButton@NormalButton>:
    canvas:
        Color:
            rgba: self.background_color
        BorderImage:
            border: self.border
            pos: self.pos
            size: self.size
            source: 'data/settings.png'
    text: ''
    border: (0, 0, 0, 0)
    size_hint_x: None
    width: self.height
    background_normal: 'data/transparent.png'
    background_down: self.background_normal

<NormalDropDown>:
    canvas.before:
        Color:
            rgba: app.theme.background
        BorderImage:
            display_border: [app.display_border, app.display_border, app.display_border, app.display_border]
            size: root.width, root.height * root.show_percent
            pos: root.pos[0], root.pos[1] + (root.height * (1 - root.show_percent)) if root.invert else root.pos[1]
            source: 'data/buttonflat.png'
""")

from globals import app_name, platform


def get_crashlog():
    """Returns the crashlog file path and name"""
    savefolder_loc, config_file_loc = get_config_file()
    crashlog = os.path.join(savefolder_loc, app_name.lower()+'_crashlog.txt')
    return crashlog


def save_current_crashlog(location):
    """Saves the last generated crashlog to the given location"""
    from shutil import copy2
    crashlog = get_crashlog()
    try:
        copy2(crashlog, location)
        return True
    except:
        return False


def save_crashlog():
    """Saves the just-generated crashlog to the current default location"""
    import traceback
    crashlog = get_crashlog()
    log_history = reversed(LoggerHistory.history)
    crashlog_file = open(crashlog, 'w')
    for log_line in log_history:
        log_line = log_line.msg
        crashlog_file.write(log_line+'\n')
    traceback_text = traceback.format_exc()
    print(traceback_text)
    crashlog_file.write(traceback_text)
    crashlog_file.close()


def get_config_file():
    """Returns [location, filename] for the config file"""
    if platform == 'win':
        savefolder = os.getenv('APPDATA') + os.path.sep + app_name
    elif platform == 'linux':
        savefolder = os.path.expanduser('~') + os.path.sep + "."+app_name.lower()
    elif platform == 'macosx':
        savefolder = os.path.expanduser('~/Library/Application Support/{}'.format(app_name))
    elif platform == 'android':
        from jnius import autoclass, cast
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        context = cast('android.content.Context', PythonActivity.mActivity)
        file_p = cast('java.io.File', context.getFilesDir())
        savefolder = file_p.getAbsolutePath()
    elif platform == 'ios':
        savefolder = os.path.expanduser(os.path.join('~/Documents', app_name))
    else:
        savefolder = os.path.join(os.path.sep, app_name)

    if not os.path.isdir(savefolder):
        os.makedirs(savefolder)
    config_file = os.path.realpath(os.path.join(savefolder, app_name.lower()+".ini"))
    return [savefolder, config_file]


def generate_seed():
    """Generates a random number seed based on the current time"""
    return int(str(time.time()).replace('.', '')[-4:])


def generate_2d_array(width, height, fillwith):
    """Creates a 2 dimensional array with the given width, height and fill object"""
    return [[fillwith] * width for i1 in range(height)]


def time_index(seconds):
    """Formats a given number of seconds in standard minutes:seconds notation"""
    all_minutes, final_seconds = divmod(seconds, 60)
    all_hours, final_minutes = divmod(all_minutes, 60)
    time_remaining = str(int(final_minutes)).zfill(2) + ':' + str(int(final_seconds)).zfill(2)
    if all_hours:
        time_remaining = str(int(all_hours)).zfill(2) + ':' + time_remaining
    return time_remaining


class Spacer(Widget):
    pass


class ReactionButton(Image):
    emotion = StringProperty('')
    can_touch = BooleanProperty(True)
    
    def on_emotion(self, *_):
        self.color = emotions_colors[self.emotion]

    def on_touch_down(self, touch):
        if not self.disabled and self.can_touch and self.collide_point(*touch.pos):
            app = App.get_running_app()
            app.multiplayer_send('reaction', [self.emotion])


class ReactionOverlay(ModalView):
    emotion = StringProperty('')
    image_x = NumericProperty(0.5)
    image_y = NumericProperty(0.5)
    image_opacity = NumericProperty(0)
    color = ListProperty([1, 1, 1])

    def on_touch_down(self, touch):
        return False

    def on_emotion(self, *_):
        self.color = emotions_colors[self.emotion]

    def end(self, *_):
        self.dismiss()

    def on_open(self):
        Clock.schedule_once(self.end, 2.25)
        anim = Animation(image_opacity=1, duration=0.25) + Animation(image_opacity=1, duration=1) + Animation(image_opacity=0, duration=1)
        anim.start(self)
        start_x = random.randrange(40, 60) / 100
        start_y = random.randrange(40, 60) / 100
        self.image_y = start_y
        self.image_x = start_x
        anim = Animation(image_y=0.9, duration=2.25)
        anim.start(self)
        wavyness = random.randrange(0, 10) / 100
        anim = Animation(image_x=start_x - wavyness, duration=.5, t='in_out_sine') + Animation(image_x=start_x + wavyness, duration=1, t='in_out_sine') + Animation(image_x=start_x - wavyness, duration=1, t='in_out_sine')
        anim.start(self)


class LayoutSplitter(GridLayout):
    owner = ObjectProperty(allownone=True)

    def __init__(self, **kwargs):
        self.owner = self
        super().__init__(**kwargs)


class HelpPopupContent(GridLayout):
    """Basic popup message with a message and 'ok' button."""

    text = ListProperty()

    def on_parent(self, *_):
        text_area = self.ids['textArea']
        text_area.clear_widgets()
        for text in self.text:
            if text == '-':
                line = Spacer()
            else:
                if not text:
                    text = ' '
                line = ChatLabel(text=text)
            text_area.add_widget(line)

    def close(self, *_):
        app = App.get_running_app()
        if app.helppopup:
            app.helppopup.dismiss()
            app.helppopup = None


class ConfirmPopupContent(BoxLayout):
    """Basic Yes/No popup message.  Calls 'on_answer' when either button is clicked."""

    text = StringProperty()
    yes_text = StringProperty('Yes')
    no_text = StringProperty('No')

    def __init__(self, **kwargs):
        self.register_event_type('on_answer')
        super(ConfirmPopupContent, self).__init__(**kwargs)

    def on_answer(self, *args):
        pass


class FillImage(Image):
    def get_filled_image_size(self):
        ratio = self.image_ratio
        w, h = self.size

        widget_ratio = w / h
        iw = (h * ratio) if ratio > widget_ratio else w
        ih = (w / ratio) if ratio <= widget_ratio else h
        return iw, ih

    norm_image_size = AliasProperty(get_filled_image_size, bind=('texture', 'size', 'allow_stretch', 'image_ratio', 'keep_ratio'), cache=True)


class ScreenLayout(BoxLayout, FillImage):
    """Special BoxLayout that has an image background"""
    pass


class StencilBox(BoxLayout, StencilView):
    """Basic combination of a BoxLayout and StencilView, used to reduce widget tree height"""
    pass


class TetraScreen(Screen):
    """Base class for the various screen widgets"""

    first_selected = ObjectProperty(allownone=True)

    def back(self):
        pass

    def on_pre_enter(self):
        app = App.get_running_app()
        app.clear_selected_overlay()

    def selected_left(self):
        try:
            app = App.get_running_app()
            app.selected_object.decrease()
        except:
            pass

    def selected_right(self):
        try:
            app = App.get_running_app()
            app.selected_object.increase()
        except:
            pass

    def selected_next(self):
        app = App.get_running_app()
        if app.selected_object is None:
            app.set_current_selected(self, self.first_selected)
        else:
            app.selected_next(self)

    def selected_prev(self):
        app = App.get_running_app()
        if app.selected_object is None:
            app.set_current_selected(self, self.first_selected)
        else:
            app.selected_prev(self)

    def dismiss(self):
        pass

    def key(self, key, down):
        if down:
            app = App.get_running_app()
            action = app.navigation_key(key)
            if action == 'next':
                self.selected_next()
            elif action == 'prev':
                self.selected_prev()
            elif action == 'enter':
                app.activate_selected()
            elif action == 'back':
                self.back()
            elif action == 'left':
                self.selected_left()
            elif action == 'right':
                self.selected_right()


class Countdown(BoxLayout):
    """Displays a large countdown text"""

    count_from = NumericProperty(3)
    countdown = NumericProperty(3)
    counter = ObjectProperty(allownone=True)
    bg_color = ListProperty([0.5, 0.5, 0.5, 1])

    def __init__(self, **kwargs):
        self.register_event_type('on_count_finished')
        super().__init__(**kwargs)

    def cancel(self):
        if self.counter is not None:
            self.counter.cancel()
            self.counter = None

    def start(self):
        self.countdown = self.count_from
        self.counter = Clock.schedule_once(self.count_less, 1)

    def count_less(self, *_):
        self.countdown -= 1
        if self.countdown == 1:
            anim = Animation(bg_color=[0.5, 0.5, 0.5, 0], duration=1)
            anim.start(self)
        if self.countdown > 0:
            self.counter = Clock.schedule_once(self.count_less, 1)
        else:
            self.dispatch('on_count_finished')

    def on_count_finished(self, *_):
        pass


class Scroller(ScrollView):
    """Generic scroller container widget."""
    pass


class NormalRecycleView(RecycleView):
    def scroll_to_index(self, index):
        box = self.children[0]
        pos_index = (box.default_size[1] + box.spacing) * index
        scroll = self.convert_distance_to_scroll(0, pos_index - (self.height * 0.5))[1]
        if scroll > 1.0:
            scroll = 1.0
        elif scroll < 0.0:
            scroll = 0.0
        self.scroll_y = 1.0 - scroll


class NormalPopup(Popup):
    """Basic popup widget."""

    first_selected = ObjectProperty(allownone=True)

    def selected_next(self):
        app = App.get_running_app()
        if app.selected_object is None:
            app.set_current_selected(self.content, self.first_selected)
        else:
            app.selected_next(self)

    def selected_prev(self):
        app = App.get_running_app()
        if app.selected_object is None:
            app.set_current_selected(self.content, self.first_selected)
        else:
            app.selected_prev(self)

    def key(self, key, down):
        if down:
            app = App.get_running_app()
            action = app.navigation_key(key)
            if action == 'next':
                self.selected_next()
            elif action == 'prev':
                self.selected_prev()
            elif action == 'enter':
                app.activate_selected()
            elif action == 'back':
                self.content.dispatch('on_cancel')
            elif action == 'left':
                try:
                    self.content.left()
                except:
                    pass
            elif action == 'right':
                try:
                    self.content.right()
                except:
                    pass

    def open(self, *args, **kwargs):
        app = App.get_running_app()
        self.opacity = 0
        anim = Animation(opacity=1, duration=app.animation_length)
        anim.bind(on_complete=self.finish_open)
        anim.start(self)
        super(NormalPopup, self).open(*args, **kwargs)

    def finish_open(self, *_):
        self.opacity = 1

    def dismiss(self, *args, **kwargs):
        app = App.get_running_app()
        anim = Animation(opacity=0, duration=app.animation_length)
        anim.start(self)
        anim.bind(on_complete=self.finish_dismiss)

    def finish_dismiss(self, *_):
        super(NormalPopup, self).dismiss()


class SpecialSlider(Slider):
    selectable_item = BooleanProperty(True)

    def decrease(self):
        new_value = self.value - .1
        if new_value < self.min:
            self.value = self.min
        else:
            self.value = new_value

    def increase(self):
        new_value = self.value + .1
        if new_value > self.max:
            self.value = self.max
        else:
            self.value = new_value

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.is_double_tap:
            #self.reset_value()
            Clock.schedule_once(self.reset_value, 0.15)  #need to delay this more than the scrollview scroll_timeout so it actually works
            return
        super(SpecialSlider, self).on_touch_down(touch)

    def reset_value(self, *_):
        pass


class NormalSlider(SpecialSlider):
    pass


#Text Inputs
class NormalInput(TextInput):
    helptext = ListProperty()
    selectable_item = BooleanProperty(True)
    messed_up_coords = BooleanProperty(False)
    long_press_time = NumericProperty(1)
    long_press_schedule = None

    def on_touch_up(self, touch):
        if self.long_press_schedule:
            self.long_press_schedule.cancel()
            self.long_press_schedule = None
        return super().on_touch_up(touch)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if hasattr(touch, 'button') and touch.button == 'right':
                if self.helptext:
                    self.long_press(touch)
                return
            if self.helptext:
                self.long_press_schedule = Clock.schedule_once(lambda x: self.long_press(touch), self.long_press_time)
        return super(NormalInput, self).on_touch_down(touch)

    def long_press(self, touch):
        if self.collide_point(*touch.pos):
            app = App.get_running_app()
            app.help(self.helptext)


class NormalInputChat(NormalInput):
    max_characters = NumericProperty(150)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        app = App.get_running_app()
        if keycode[0] == 27:
            self.focus = False
            return True
        if keycode[0] in [13, 271]:
            app.multiplayer_send_message()
            return True
        super().keyboard_on_key_down(window, keycode, text, modifiers)

    def on_text(self, *_):
        app = App.get_running_app()
        text_length = len(self.text)
        if text_length > 0:
            app.multiplayer_send('chat typing', [])
        elif text_length == 0:
            app.multiplayer_send('chat not typing', [])

    def insert_text(self, substring, from_undo=False):
        text_length = len(self.text)
        if text_length > self.max_characters:
            substring = ""
        return super().insert_text(substring, from_undo=from_undo)


class FloatInput(NormalInput):
    selectable_item = BooleanProperty(True)
    pat = re.compile('[^0-9]')

    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        if '.' in self.text:
            s = re.sub(pat, '', substring)
        else:
            s = '.'.join([re.sub(pat, '', s) for s in substring.split('.', 1)])
        return super().insert_text(s, from_undo=from_undo)


class IntegerInput(NormalInput):
    selectable_item = BooleanProperty(True)
    pat = re.compile('[^0-9]')

    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        s = re.sub(pat, '', substring)
        return super().insert_text(s, from_undo=from_undo)


class IPInput(NormalInput):
    selectable_item = BooleanProperty(True)
    pat = re.compile('[^0-9]')

    def insert_text(self, substring, from_undo=False):
        if substring == '.':
            s = substring
        else:
            pat = self.pat
            s = re.sub(pat, '', substring)
        return super().insert_text(s, from_undo=from_undo)


#Labels
class NormalLabel(Label):
    """Basic label widget"""
    pass


class FastForwardLabel(NormalLabel):
    """Label that blinks to show the fast forward text"""

    activate = NumericProperty()
    animation = ObjectProperty(allownone=True)

    def cancel_animation(self):
        if self.animation is not None:
            self.animation.stop(self)
            self.animation = None

    def on_activate(self, *_):
        if self.activate > 1:
            self.opacity = 1
            self.cancel_animation()
            self.animation = Animation(duration=0.2) + Animation(opacity=0, duration=0.2)
            self.animation.start(self)


class ShortLabel(NormalLabel):
    """Label widget that will remain the minimum width"""
    pass


class LeftNormalLabel(NormalLabel):
    """Label widget that displays text left-justified"""
    pass


class ChatLabel(RecycleDataViewBehavior, NormalLabel):
    index = NumericProperty(0)

    def update_height(self, *_):
        self.height = self.texture_size[1]

    def refresh_view_attrs(self, rv, index, data):
        Clock.schedule_once(self.update_height, -1)
        self.index = index
        return super().refresh_view_attrs(rv, index, data)


class InfoLabel(NormalLabel):
    bgcolor = ListProperty([1, 1, 0, 0])
    blinker = ObjectProperty()

    def on_text(self, instance, text):
        del instance
        app = App.get_running_app()
        if self.blinker:
            self.stop_blinking()
        if text:
            no_bg = [.5, .5, .5, 0]
            yes_bg = app.theme.info_background
            self.blinker = Animation(bgcolor=yes_bg, duration=0.33) + Animation(bgcolor=no_bg, duration=0.33) + Animation(bgcolor=yes_bg, duration=0.33) + Animation(bgcolor=no_bg, duration=0.33) + Animation(bgcolor=yes_bg, duration=0.33) + Animation(bgcolor=no_bg, duration=0.33) + Animation(bgcolor=yes_bg, duration=0.33) + Animation(bgcolor=no_bg, duration=0.33) + Animation(bgcolor=yes_bg, duration=0.33) + Animation(bgcolor=no_bg, duration=0.33) + Animation(bgcolor=yes_bg, duration=0.33) + Animation(bgcolor=no_bg, duration=0.33) + Animation(bgcolor=yes_bg, duration=0.33) + Animation(bgcolor=no_bg, duration=0.33)
            self.blinker.start(self)

    def stop_blinking(self, *_):
        if self.blinker:
            self.blinker.cancel(self)
        self.bgcolor = [1, 1, 0, 0]


#Buttons
class ButtonBase(Button):
    """Basic button widget."""

    selectable_item = BooleanProperty(True)
    warn = BooleanProperty(False)
    target_background = ListProperty()
    target_text = ListProperty()
    background_animation = ObjectProperty()
    text_animation = ObjectProperty()
    last_disabled = False
    menu = BooleanProperty(False)
    toggle = BooleanProperty(False)
    long_press_time = NumericProperty(1)
    long_press_schedule = ObjectProperty(allownone=True)
    long_press_queued = BooleanProperty(False)
    helptext = ListProperty()

    button_update = BooleanProperty()

    def __init__(self, **kwargs):
        self.background_animation = Animation()
        self.text_animation = Animation()
        app = App.get_running_app()
        self.background_color = app.theme.button_up
        self.target_background = self.background_color
        self.color = app.theme.button_text
        self.target_text = self.color
        super(ButtonBase, self).__init__(**kwargs)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if hasattr(touch, 'button') and touch.button == 'right':
                if self.helptext:
                    self.long_press(touch)
                return
            if self.helptext:
                self.long_press_queued = False
                self.long_press_schedule = Clock.schedule_once(lambda x: self.long_press(touch), self.long_press_time)
        super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.long_press_schedule:
            self.long_press_schedule.cancel()
            self.long_press_schedule = None
        if not self.long_press_queued:
            super().on_touch_up(touch)
        else:
            self._do_release()
            touch.ungrab(self)

    def long_press(self, touch):
        if self.collide_point(*touch.pos):
            self.long_press_queued = True
            app = App.get_running_app()
            app.help(self.helptext)

    def on_button_update(self, *_):
        Clock.schedule_once(self.set_color_instant)

    def set_color_instant(self, *_):
        self.set_color(instant=True)

    def set_color(self, instant=False):
        app = App.get_running_app()
        if self.disabled:
            self.set_text(app.theme.button_disabled_text, instant=instant)
            self.set_background(app.theme.button_disabled, instant=instant)
        else:
            self.set_text(app.theme.button_text, instant=instant)
            if self.menu:
                if self.state == 'down':
                    self.set_background(app.theme.button_down, instant=True)
                else:
                    self.set_background(app.theme.button_up, instant=instant)
            elif self.toggle:
                if self.state == 'down':
                    self.set_background(app.theme.button_toggle_true, instant=instant)
                else:
                    self.set_background(app.theme.button_toggle_false, instant=instant)

            elif self.warn:
                if self.state == 'down':
                    self.set_background(app.theme.button_warn_down, instant=True)
                else:
                    self.set_background(app.theme.button_warn_up, instant=instant)
            else:
                if self.state == 'down':
                    self.set_background(app.theme.button_down, instant=True)
                else:
                    self.set_background(app.theme.button_up, instant=instant)

    def on_disabled(self, *_):
        self.set_color()

    def on_menu(self, *_):
        self.set_color(instant=True)

    def on_toggle(self, *_):
        self.set_color(instant=True)

    def on_warn(self, *_):
        self.set_color(instant=True)

    def on_state(self, *_):
        self.set_color()

    def set_background(self, color, instant=False):
        if self.target_background == color:
            return
        app = App.get_running_app()
        self.background_animation.stop(self)
        if app.animations and not instant:
            self.background_animation = Animation(background_color=color, duration=app.animation_length)
            self.background_animation.start(self)
        else:
            self.background_color = color
        self.target_background = color

    def set_text(self, color, instant=False):
        if self.target_text == color:
            return
        app = App.get_running_app()
        self.text_animation.stop(self)
        if app.animations and not instant:
            self.text_animation = Animation(color=color, duration=app.animation_length)
            self.text_animation.start(self)
        else:
            self.color = color
        self.target_text = color


class ToggleBase(ToggleButton, ButtonBase):
    pass


class IndexToggle(ToggleBase):
    """ToggleButton with added index value, used for music selections."""

    index = NumericProperty()


class NormalButton(ButtonBase):
    """Basic button widget."""
    pass


class WideButton(ButtonBase):
    """Full width button widget"""
    pass


class MenuButton(ButtonBase):
    """Basic class for a drop-down menu button item."""
    pass


class NormalDropDown(DropDown):
    """Dropdown menu class with some nice animations."""

    show_percent = NumericProperty(1)
    invert = BooleanProperty(False)
    basic_animation = BooleanProperty(False)

    def open(self, *args, **kwargs):
        if self.parent:
            self.dismiss()
            return
        app = App.get_running_app()
        super(NormalDropDown, self).open(*args, **kwargs)

        if app.animations:
            if self.basic_animation:
                #Dont do fancy child opacity animation
                self.opacity = 0
                self.show_percent = 1
                anim = Animation(opacity=1, duration=app.animation_length)
                anim.start(self)
            else:
                #determine if we opened up or down
                attach_to_window = self.attach_to.to_window(*self.attach_to.pos)
                if attach_to_window[1] > self.pos[1]:
                    self.invert = True
                    children = reversed(self.container.children)
                else:
                    self.invert = False
                    children = self.container.children

                #Animate background
                self.opacity = 1
                self.show_percent = 0
                anim = Animation(show_percent=1, duration=app.animation_length)
                anim.start(self)

                if len(self.container.children) > 0:
                    item_delay = app.animation_length / len(self.container.children)
                else:
                    item_delay = 0

                for i, w in enumerate(children):
                    anim = (Animation(duration=i * item_delay) + Animation(opacity=1, duration=app.animation_length))
                    w.opacity = 0
                    anim.start(w)
        else:
            self.opacity = 1

    def dismiss(self, *args, **kwargs):
        app = App.get_running_app()
        if app.animations:
            anim = Animation(opacity=0, duration=app.animation_length)
            anim.start(self)
            anim.bind(on_complete=self.finish_dismiss)
        else:
            self.finish_dismiss()

    def finish_dismiss(self, *_):
        super(NormalDropDown, self).dismiss()
