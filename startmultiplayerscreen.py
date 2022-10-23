from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import AliasProperty, ObjectProperty, StringProperty, ListProperty, BooleanProperty, NumericProperty, DictProperty
from generalelements import ConfirmPopupContent, NormalPopup, ChatLabel, generate_seed, NormalDropDown, MenuButton, IPInput, IntegerInput
from globals import multiplayer_port
from startscreens import GameStartScreen

from kivy.lang.builder import Builder
Builder.load_string("""
<AddressPreset>:
    orientation: 'horizontal'
    padding: app.button_scale / 2, 0
    WideButton:
        disabled: True if app.mp_connection is None else False
        text: root.ip
        on_release: app.mp_connection.remote_ip = root.ip
        on_release: root.parent.screen_manager.current = 'main'

<MultiplayerScreen>:
    first_selected: first_select
    disabled: self.starting_game
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
                text: 'Multiplayer'
            SettingsButton:
                on_release: app.show_settings('multiplayer')
        BoxLayout:
            padding: app.screen_border
            ScreenManager:
                transition: SlideTransition(direction='up')
                id: screen_manager
                Screen:
                    name: 'main'
                    BoxLayout:
                        orientation: 'vertical'
                        WideButton:
                            font_size: app.text_scale * 1.5
                            size_hint_y: None
                            height: app.button_scale * 1.5
                            text: 'Start Game'
                            disabled: not root.connected
                            on_release: root.start_game()
                        LayoutSplitter:
                            size_hint_y: 1
                            owner: root
                            GridLayout:
                                size_hint_y: None
                                height: self.parent.height if self.parent.wider else self.minimum_height
                                cols: 1
                                padding: app.button_scale / 2, 0
                                WideMenuStarter:
                                    disabled: app.mp_thinking
                                    size_hint_y: None
                                    height: app.button_scale
                                    helptext: ['Connection Modes:', '-', 'Local: Connect to a computer on the same network (either via WiFi or wired connection.', '', 'Port Forwarding: Ask your router to forward a port via UPnP to easily connect to a computer elsewhere.', '', 'Direct Connection: Connect to another computer via IP address.  You will most likely need to manually forward a port.', '', 'Bluetooth: Directly connect to another device over a bluetooth connection.']
                                    text: 'Connection Mode: '+app.connection_friendly(root.multiplayer_mode)
                                    on_release: root.multiplayer_mode_menu.open(self)
                                ScreenManager:
                                    canvas.before:
                                        Color:
                                            rgba: app.theme.indented
                                        BorderImage:
                                            display_border: [app.display_border, app.display_border, app.display_border, app.display_border]
                                            border: 16, 16, 16, 16
                                            size: self.size
                                            pos: self.pos
                                            source: 'data/inverted.png'
                                    size_hint_y: None
                                    height: (app.button_scale * 3) + (app.display_border * 2)
                                    id: connection_mode
                                    current: root.multiplayer_mode
                                    Screen:
                                        name: 'local'
                                        BoxLayout:
                                            padding: [app.display_border, app.display_border, app.display_border, app.display_border]
                                            orientation: 'vertical'
                                            BoxLayout:
                                                orientation: 'horizontal'
                                                size_hint_y: None
                                                height: app.button_scale
                                                ShortLabel:
                                                    text: "Your Address: "
                                                NormalInput:
                                                    helptext: ['Your Address:', '-', 'This is your IP address that other apps should connect to.  This field can be copied, but not edited.  ']
                                                    readonly: True
                                                    text: app.local_ip
                                            BoxLayout:
                                                orientation: 'horizontal'
                                                size_hint_y: None
                                                height: app.button_scale
                                                ShortLabel:
                                                    size_hint_y: None
                                                    height: app.button_scale
                                                    text: "Connect To: "
                                                IPInput:
                                                    helptext: ['Connect To:', '-', "The IP address of the other app to connect to.  This should be the same value shown in the 'Your Address' field of the other app.  "]
                                                    text: app.remote_ip
                                                    on_text: root.set_remote_ip(self.text)
                                                    disabled: app.connecting or app.connected
                                                NormalButton:
                                                    text: 'Find...'
                                                    helptext: ['Local Connection Finder:', '-', 'This button will open a list of other devices on the network that are actively seeking a connection.', 'Any other instances of this app currently on the multiplayer screen should show up in the list.']
                                                    disabled: app.connecting or app.connected
                                                    on_release: screen_manager.current = 'select'
                                                    on_release: root.current_selected = None
                                                    on_release: app.clear_selected_overlay()
                                            BoxLayout:
                                                orientation: 'horizontal'
                                                size_hint_y: None
                                                height: app.button_scale
                                                LeftNormalLabel:
                                                    text: app.connect_status
                                                WideButton:
                                                    id: first_select
                                                    text: app.connect_action
                                                    disabled: True if app.mp_connection is None else False
                                                    on_release: app.mp_connection.connect_action_call()
                                    Screen:
                                        name: 'port_forward'
                                        BoxLayout:
                                            padding: [app.display_border, app.display_border, app.display_border, app.display_border]
                                            orientation: 'vertical'
                                            BoxLayout:
                                                orientation: 'horizontal'
                                                size_hint_y: None
                                                height: app.button_scale
                                                ShortLabel:
                                                    text: "Your Address: "
                                                NormalInput:
                                                    helptext: ['Your Address:', '-', 'This is your IP address that other apps should connect to.  Please note that this address may not be detected correctly on all devices, please double-check this with a website that shows your external IP address if someone is not able to connect to you.  This field can be copied, but not edited.  ']
                                                    readonly: True
                                                    text: app.external_local_ip
                                            BoxLayout:
                                                orientation: 'horizontal'
                                                size_hint_y: None
                                                height: app.button_scale
                                                ShortLabel:
                                                    size_hint_y: None
                                                    height: app.button_scale
                                                    text: "Connect To: "
                                                IPInput:
                                                    helptext: ['Connect To:', '-', "The IP address of the other app to connect to.  This should be the same value shown in the 'Your Address' field of the other app.  "]
                                                    text: app.remote_ip
                                                    on_text: root.set_remote_ip(self.text)
                                                    disabled: app.connecting or app.connected
                                                ShortLabel:
                                                    size_hint_y: None
                                                    height: app.button_scale
                                                    text: ":"
                                                IntegerInput:
                                                    helptext: ['Connect To:', '-', 'The port number to connect to.  This must be set to the same number for both instances of the app, and this port must not be in use by another program or computer on your network.  ']
                                                    size_hint_x: 0.5
                                                    text: str(app.port)
                                                    on_focus: root.set_port(self, self.text)
                                                    disabled: app.connecting or app.connected
                                            BoxLayout:
                                                orientation: 'horizontal'
                                                size_hint_y: None
                                                height: app.button_scale
                                                LeftNormalLabel:
                                                    text: app.connect_status
                                                WideButton:
                                                    id: first_select
                                                    text: app.connect_action
                                                    disabled: True if app.mp_connection is None or app.mp_thinking else False
                                                    on_release: app.mp_connection.connect_action_call()
                                    Screen:
                                        name: 'direct'
                                        BoxLayout:
                                            padding: [app.display_border, app.display_border, app.display_border, app.display_border]
                                            orientation: 'vertical'
                                            BoxLayout:
                                                orientation: 'horizontal'
                                                size_hint_y: None
                                                height: app.button_scale
                                                ShortLabel:
                                                    text: "Your Address: "
                                                NormalInput:
                                                    helptext: ['Your Address:', '-', 'This is your IP address that other apps should connect to.  Please note that this address may not be detected correctly on all devices, please double-check this with a website that shows your external IP address if someone is not able to connect to you.  This field can be copied, but not edited.  ']
                                                    readonly: True
                                                    text: app.external_local_ip
                                            BoxLayout:
                                                orientation: 'horizontal'
                                                size_hint_y: None
                                                height: app.button_scale
                                                ShortLabel:
                                                    size_hint_y: None
                                                    height: app.button_scale
                                                    text: "Connect To: "
                                                IPInput:
                                                    helptext: ['Connect To:', '-', "The IP address of the other app to connect to.  This should be the same value shown in the 'Your Address' field of the other app.  "]
                                                    text: app.remote_ip
                                                    on_text: root.set_remote_ip(self.text)
                                                    disabled: app.connecting or app.connected
                                                ShortLabel:
                                                    size_hint_y: None
                                                    height: app.button_scale
                                                    text: ":"
                                                IntegerInput:
                                                    helptext: ['Connect To:', '-', 'The port number to connect to.  This must be set to the same number for both instances of the app, and this port must not be in use by another program or computer on your network.  ']
                                                    size_hint_x: 0.5
                                                    text: str(app.port)
                                                    on_focus: root.set_port(self, self.text)
                                                    disabled: app.connecting or app.connected
                                            BoxLayout:
                                                orientation: 'horizontal'
                                                size_hint_y: None
                                                height: app.button_scale
                                                LeftNormalLabel:
                                                    text: app.connect_status
                                                WideButton:
                                                    id: first_select
                                                    text: app.connect_action
                                                    disabled: True if app.mp_connection is None or app.mp_thinking else False
                                                    on_release: app.mp_connection.connect_action_call()
                                    Screen:
                                        name: 'bluetooth'
                                        BoxLayout:
                                            padding: [app.display_border, app.display_border, app.display_border, app.display_border]
                                            orientation: 'vertical'
                                            NormalLabel:
                                                text: 'Not implemented yet'
                                BoxLayout:
                                    orientation: 'horizontal'
                                    height: app.button_scale if self.parent.parent.wider else (app.button_scale / 2)
                                    size_hint_y: None
                                    LeftNormalLabel:
                                        text: "Game Speed:"
                                    LeftNormalLabel:
                                        text: 'Opponent: '+str(root.other_speed)
                                SmoothSetting:
                                    size_hint_y: None
                                    height: app.button_scale * .75
                                    item_width: app.button_scale
                                    control_width: app.button_scale * 0.75
                                    start_on: root.speed
                                    on_active: root.speed = self.active
                                    helptext: ['Game Speed:', '-', 'This defines the starting speed level for your game.  Lines completed will increase your level, but your speed will not increase until you surpass this starting level.  ', '', 'When connected to an opponent, the game speed selected by your opponent will be visible above this slider.  ']
                                    content: ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15']
                                BoxLayout:
                                    orientation: 'horizontal'
                                    height: app.button_scale if self.parent.parent.wider else (app.button_scale / 2)
                                    size_hint_y: None
                                    LeftNormalLabel:
                                        text: "Filled Lines:"
                                    LeftNormalLabel:
                                        text: 'Opponent: '+str(root.other_filled)
                                SmoothSetting:
                                    size_hint_y: None
                                    height: app.button_scale * .75
                                    item_width: app.button_scale
                                    helptext: ['Filled Lines:', '-', 'This sets a number of lines to be filled with garbage blocks at the start of the game.  For each level of filled lines, two garbage lines will be added to the bottom of the field.  ', '', 'When connected to an opponent, the filled lines selected by your opponent will be visible above this slider.  ']
                                    control_width: app.button_scale * 0.75
                                    start_on: root.filled
                                    on_active: root.filled = self.active
                                    content: ['0', '1', '2', '3', '4', '5']
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
                        FloatLayout:
                            size_hint_y: None
                            disabled: False if app.connected else True
                            height: app.button_scale * 2 if not self.disabled else 1
                            opacity: 0 if self.disabled else 1
                            NormalRecycleView:
                                canvas.before:
                                    Color:
                                        rgba: app.theme.indented
                                    BorderImage:
                                        display_border: [app.display_border, app.display_border, app.display_border, app.display_border]
                                        border: 16, 16, 16, 16
                                        size: self.size
                                        pos: self.pos
                                        source: 'data/inverted.png'
                                scroll_y: 0
                                do_scroll_x: False
                                size_hint: None, None
                                pos: self.parent.pos
                                size: self.parent.size
                                id: chatArea
                                data: app.multiplayer_text
                                viewclass: 'ChatLabel'
                                RecycleBoxLayout:
                                    padding: app.button_scale / 4, app.button_scale / 10
                                    default_size_hint: 1, None
                                    orientation: 'vertical'
                                    size_hint_y: None
                                    height: self.minimum_height
                            Image:
                                size_hint: None, None
                                size: app.button_scale / 2, app.button_scale / 6.666
                                color: app.theme.button_text if app.multiplayer_typing else (1, 1, 1, 0)
                                anim_delay: 0.0333
                                pos: self.parent.pos[0] + self.parent.size[0] - self.size[0], self.parent.pos[1]
                                source: 'data/elipsis.zip'
                        BoxLayout:
                            disabled: not app.connected
                            size_hint_y: None
                            height: 1 if self.disabled else app.button_scale
                            opacity: 0 if self.disabled else 1
                            NormalInputChat:
                                multiline: False
                                hint_text: 'Type A Message To Your Opponent'
                                text: app.multiplayer_text_current
                                on_text: app.multiplayer_text_current = self.text
                            NormalButton:
                                text: 'Send'
                                on_release: app.multiplayer_send_message()

                Screen:
                    name: 'select'
                    BoxLayout:
                        orientation: 'vertical'
                        WideButton:
                            text: 'Cancel'
                            on_release: screen_manager.current = 'main'
                            on_release: root.current_selected = None
                            on_release: app.clear_selected_overlay()
                            size_hint_y: None
                            height: app.button_scale
                        NormalRecycleView:
                            data: app.available_addresses
                            viewclass: 'AddressPreset'
                            RecycleBoxLayout:
                                screen_manager: screen_manager
                                default_size: None, app.button_scale
                                default_size_hint: 1, None
                                orientation: 'vertical'
                                size_hint_y: None
                                height: self.minimum_height
""")


class AddressPreset(BoxLayout):
    """Viewclass to display addresses to connect to in the multiplayer screen."""
    ip = StringProperty()
    refresh_time = NumericProperty()


class MultiplayerScreen(GameStartScreen):
    """Screen for settings for a multiplayer game"""

    starting_game = BooleanProperty(False)

    game_seed = 0
    speed = NumericProperty(0)
    filled = NumericProperty(0)
    other_speed = NumericProperty(0)
    other_filled = NumericProperty(0)
    multiplayer_mode_menu = ObjectProperty()

    popup_dismisser = ObjectProperty(allownone=True)
    popup = ObjectProperty(allownone=True)
    multiplayer_mode = StringProperty('')

    def __init__(self, **kwargs):
        self.register_event_type('on_filled')
        self.register_event_type('on_speed')
        super().__init__(**kwargs)

    def back(self):
        app = App.get_running_app()
        app.multiplayer_stop()
        app.main()

    def dismiss(self):
        app = App.get_running_app()
        return app.dismiss_popup()

    def set_remote_ip(self, ip):
        app = App.get_running_app()
        if app.mp_connection is not None:
            app.mp_connection.remote_ip = ip

    def set_port(self, textinput, port):
        if textinput.focus:
            return
        app = App.get_running_app()
        if app.mp_connection is not None:
            try:
                port = int(float(port))
            except Exception as e:
                port = multiplayer_port
                app.port = port
            if port == 0:
                port = multiplayer_port
                app.port = port
            app.mp_connection.port = port
            if port != app.mp_connection.forwarded_port:
                app.mp_connection.restart('scanning')

    def stop_game_start(self, *_):
        self.starting_game = False

    def connected(self, *_):
        self.on_filled()
        self.on_speed()

    def ask_connect(self, *_):
        Clock.schedule_once(self.ask_connect_delay)

    def ask_connect_delay(self, *_):
        app = App.get_running_app()
        if app.popup:
            return
        content = ConfirmPopupContent(text=app.mp_connection.connect_ip+' wants to connect for multiplayer, accept?', yes_text='Connect', no_text="Don't Connect")
        content.bind(on_answer=self.accept_connection_answer)
        app.popup = NormalPopup(title="Accept Connection?", content=content, size_hint=(1, None), size=(1000, app.button_scale * 3), auto_dismiss=False)
        app.popup.bind(on_dismiss=app.dismiss_popup)
        app.popup.open()
        self.popup_timeout_cancel()
        self.popup_dismisser = Clock.schedule_once(self.popup_timeout, 30)

    def popup_timeout_cancel(self):
        if self.popup_dismisser:
            self.popup_dismisser.cancel()
            self.popup_dismisser = None

    def popup_timeout(self, *_):
        app = App.get_running_app()
        app.dismiss_popup()
        self.popup_dismisser = None
        app.mp_connection.refuse_connect(block=False)

    def accept_connection_answer(self, instance, answer):
        app = App.get_running_app()
        app.dismiss_popup()
        self.popup_timeout_cancel()
        if answer == 'yes':
            app.mp_connection.connect_to()
        else:
            app.mp_connection.refuse_connect()

    def set_multiplayer_mode(self, mode):
        self.multiplayer_mode_menu.dismiss()
        if mode in ['local', 'port_forward', 'direct', 'bluetooth']:
            self.multiplayer_mode = mode
        else:
            self.multiplayer_mode = 'local'
        app = App.get_running_app()
        app.multiplayer_stop()
        app.multiplayer_start()
        app.mp_connection.remote_ip = app.config.get('Settings', 'last_multiplayer')
        if mode != 'local':
            try:
                port = int(float(app.config.get('Settings', 'last_multiplayer_port')))
            except Exception as e:
                port = multiplayer_port
                app.port = port
            if port == 0:
                port = multiplayer_port
                app.port = port
            app.mp_connection.port = port
        else:
            app.mp_connection.port = multiplayer_port
        app.mp_ready_start = False
        if app.mp_connection is None:
            app.main()
            app.message('No Internet\nPermissions!')
            return
        app.mp_connection.connect_mode = self.multiplayer_mode
        app.mp_connection.restart('scanning')

    def on_enter(self):
        app = App.get_running_app()
        self.multiplayer_mode_menu = NormalDropDown()
        menu_button = MenuButton(text='Local Network')
        menu_button.bind(on_release=lambda x: self.set_multiplayer_mode('local'))
        self.multiplayer_mode_menu.add_widget(menu_button)
        menu_button = MenuButton(text='Port Forward Remote')
        menu_button.bind(on_release=lambda x: self.set_multiplayer_mode('port_forward'))
        self.multiplayer_mode_menu.add_widget(menu_button)
        menu_button = MenuButton(text='Direct Remote')
        menu_button.bind(on_release=lambda x: self.set_multiplayer_mode('direct'))
        self.multiplayer_mode_menu.add_widget(menu_button)
        #menu_button = MenuButton(text='Bluetooth Connection')
        #menu_button.bind(on_release=lambda x: self.set_multiplayer_mode('bluetooth'))
        #self.multiplayer_mode_menu.add_widget(menu_button)

        if not app.connected:
            app.multiplayer_text = []
            self.set_multiplayer_mode(app.config.get('Settings', 'last_multiplayer_mode'))
        app.clear_selected_overlay()
        self.starting_game = False
        self.populate_areas()
        self.ids.screen_manager.current = 'main'

    def on_leave(self):
        app = App.get_running_app()
        app.config.set('Settings', 'last_multiplayer_mode', self.multiplayer_mode)
        app.save_multiplayer_ip()
        app.save_port()
        self.ids.screen_manager.current = 'main'
        app.stop_music()

    def on_filled(self, *_):
        app = App.get_running_app()
        app.multiplayer_send('filled set', [self.filled])

    def on_speed(self, *_):
        app = App.get_running_app()
        app.multiplayer_send('speed set', [self.speed])

    def populate_areas(self):
        self.populate_music()

    def start_game(self):
        app = App.get_running_app()
        if not app.mp_connection.connected:
            return
        self.game_seed = generate_seed()
        app.multiplayer_send('game start', [self.game_seed])
        self.starting_game = True

    def start_game_finish(self, seed=None):
        app = App.get_running_app()
        if seed is None:
            seed = self.game_seed
        app.game()
        game_screen = app.game_screen
        game_screen.start_speed = self.speed
        game_screen.start_filled = self.filled
        game_screen.periodic_add_lines = 0
        game_screen.game_mode = 'C'
        game_screen.start_game(seed=seed)

