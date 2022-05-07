import random
import time
import os

from kivy.app import App
from kivy.clock import Clock
from kivy.properties import OptionProperty, ObjectProperty, StringProperty, ListProperty, BooleanProperty, NumericProperty, DictProperty
from kivy.animation import Animation
from kivy.uix.relativelayout import RelativeLayout
from kivy.graphics import Rectangle
from kivy.graphics import Color
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image

from generalelements import TetraScreen, ReactionButton, ChatLabel, Countdown, generate_2d_array, time_index, generate_seed

from kivy.lang.builder import Builder
Builder.load_string("""
<GameScreen>:
    ScreenLayout:
        pos: root.pos
        size: root.size
        size_hint: None, None
        orientation: 'vertical'
        Header:
            NormalButton:
                text: '  Back  '
                on_release: root.back()
            WideButton:
                text: 'Unpause Game' if root.paused and not root.unpausing else 'Pause Game'
                disabled: True if (not root.game_running) else False
                on_release: root.pause()
            WideButton:
                text: 'End Game' if root.game_running else 'New Game'
                disabled: True if root.replay or (not root.game_running and root.game_mode == 'C') else False
                on_release: root.toggle_game()
            InfoLabel:
            SettingsButton:
                on_release: app.show_settings('game')
        BoxLayout:
            padding: app.screen_border, 0, app.screen_border, app.screen_border
            PlayLayout:
                id: playLayout
                owner: root
                field_height: root.field_height
                field_width: root.field_width
                GridLayout:
                    cols: max(1, round((self.width / self.height) * 2.5))
                    id: reactionArea
                    spacing: app.button_scale / 4
                    size_hint: None, None
                    ReactionButton:
                        emotion: 'happy'
                    ReactionButton:
                        emotion: 'unamused'
                    ReactionButton:
                        emotion: 'mad'
                    ReactionButton:
                        emotion: 'surprised'
                    ReactionButton:
                        emotion: 'evil'
                    ReactionButton:
                        emotion: 'sad'
                BoxLayout:
                    canvas.before:
                        Color:
                            rgba: app.theme.darkened[0], app.theme.darkened[1], app.theme.darkened[2], (0 if self.orientation == 'vertical' else app.theme.darkened[3])
                        Rectangle:
                            size: self.size
                            pos: self.pos
                        Color:
                            rgba: app.theme.indented[0], app.theme.indented[1], app.theme.indented[2], (0 if self.orientation == 'horizontal' else app.theme.indented[3])
                        BorderImage:
                            display_border: [app.display_border, app.display_border, app.display_border, app.display_border]
                            border: 16, 16, 16, 16
                            size: self.size
                            pos: self.pos
                            source: 'data/inverted.png'
                    id: scoreArea
                    size_hint: None, None
                    padding: 0, 0
                    orientation: 'horizontal'
                    NormalLabel:
                        text: 'Score: '+str(root.score)
                    NormalLabel:
                        text: 'Remaining:'+str(root.remaining_lines) if root.game_mode == 'B' else 'Lines: '+str(root.completed_lines)
                    NormalLabel:
                        text: 'Level: '+str(root.level)+('+'+str(root.level_offset_real) if root.level_offset_real else '')
                    NormalLabel:
                        text: 'Time: '+app.format_frames(root.total_ticks)
                BoxLayout:
                    id: extraArea
                    size_hint: None, None
                    padding: app.button_scale / 2
                    Image:
                        source: 'data/icon.png'
                BoxLayout:
                    id: nameArea
                    size_hint: None, None
                    padding: app.button_scale / 2
                    Image:
                        source: 'data/appname.png'
                StencilBox:
                    id: playAreaBox
                    size_hint: None, None
                    padding: app.display_border / 2, app.display_border / 2
                    canvas.before:
                        Color:
                            rgba: app.theme.indented
                        BorderImage:
                            display_border: [app.display_border, app.display_border, app.display_border, app.display_border]
                            border: 16, 16, 16, 16
                            size: self.size
                            pos: self.pos
                            source: 'data/inverted.png'
                    RelativeLayout:
                        PlayArea:
                            paused: root.paused and not root.unpausing
                            opacity: 0 if self.paused else 1
                            id: playArea
                            size_hint_y: None
                            pos: overlayArea.pos
                            height: overlayArea.height
                        Widget:
                            canvas.before:
                                Color:
                                    rgba: 1, 0, 0, .3
                                Rectangle:
                                    size: self.size
                                    pos: self.pos
                            size_hint_y: len(root.lines_to_add) / root.field_height
                        Widget:
                            canvas:
                                Color:
                                    rgba: 1, 0, 0, .5
                                Rectangle:
                                    pos: self.pos[0] + self.width, self.pos[1]
                                    size: 6, self.height * (root.opponent_block_height / root.field_height)
                        BoxLayout:
                            orientation: 'vertical'
                            RelativeLayout:
                                id: overlayArea
                                WideButton:
                                    disabled: not root.paused
                                    on_release: root.pause()
                                    opacity: 1 - playArea.pause_opacity
                                Image:
                                    opacity: 1 - playArea.pause_opacity
                                    source: 'data/paused.png'
                                FastForwardLabel:
                                    activate: root.playback_speed
                                TouchControl:
                                    invisible: True
                            BoxLayout:
                                size_hint_y: None
                                disabled: not (root.show_chat and app.connected)
                                opacity: 0 if self.disabled else 1
                                height: 0 if self.disabled else (app.button_scale * 5)
                                orientation: 'vertical'
                                FloatLayout:
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
                                    size_hint_y: None
                                    height: app.button_scale
                                    NormalInputChat:
                                        multiline: False
                                        hint_text: 'Type A Message To Your Opponent'
                                        text: app.multiplayer_text_current
                                        on_text: app.multiplayer_text_current = self.text
                                    NormalButton:
                                        text: 'Send'
                                        on_release: app.multiplayer_send_message()
                FloatLayout:
                    canvas.before:
                        Color:
                            rgba: app.theme.indented
                        BorderImage:
                            display_border: [app.display_border, app.display_border, app.display_border, app.display_border]
                            border: 16, 16, 16, 16
                            size: self.size
                            pos: self.pos
                            source: 'data/inverted.png'
                    id: nextArea
                    size_hint: None, None
                    PieceDisplay:
                        pos: self.parent.pos
                        size: self.parent.size
                        cols: 1
                        padding: self.width / (self.cols + 1)
                        id: nextPiece
                    LeftNormalLabel:
                        padding: 15, 15
                        valign: 'top'
                        pos: self.parent.pos
                        size: self.parent.size
                        text: 'Next:'
                    TouchArea:
                        function: 'down'
                        show_image: False
                        pos: self.parent.pos
                FloatLayout:
                    canvas.before:
                        Color:
                            rgba: app.theme.indented
                        BorderImage:
                            display_border: [app.display_border, app.display_border, app.display_border, app.display_border]
                            border: 16, 16, 16, 16
                            size: self.size
                            pos: self.pos
                            source: 'data/inverted.png'
                    id: storedArea
                    size_hint: None, None
                    PieceDisplay:
                        cols: 1
                        padding: self.width / (self.cols + 1)
                        pos: self.parent.pos
                        size: self.parent.size
                        id: storedPiece
                    LeftNormalLabel:
                        pos: self.parent.pos
                        size: self.parent.size
                        padding: 15, 15
                        valign: 'top'
                        text: 'Stored:'
                    TouchButton:
                        opacity: 0
                        pos: self.parent.pos
                        on_press: root.store()
                TouchDrop:
                    id: hardDownButton
                    size_hint: None, None
                    disabled: False if app.touch_area else True
                    opacity: 0 if self.disabled else 1
                    on_press: root.hard_down(safe=True)
                TouchButton:
                    id: rotateLeftButton
                    disabled: not app.touch_rotate
                    opacity: 0 if self.disabled else 1
                    size_hint: None, None
                    image: 'data/rotatel.png'
                    on_press: root.rotate_left()
                TouchArea:
                    id: moveLeftButton
                    disabled: not app.touch_slide
                    opacity: 0 if self.disabled else 1
                    size_hint: None, None
                    function: 'left'
                    image: 'data/left.png'
                TouchArea:
                    id: moveDownButton
                    size_hint: None, None
                    function: 'down'
                    image: 'data/down.png'
                TouchArea:
                    id: moveRightButton
                    disabled: not app.touch_slide
                    opacity: 0 if self.disabled else 1
                    size_hint: None, None
                    function: 'right'
                    image: 'data/right.png'
                TouchButton:
                    id: rotateRightButton
                    disabled: not app.touch_rotate
                    opacity: 0 if self.disabled else 1
                    size_hint: None, None
                    image: 'data/rotater.png'
                    on_press: root.rotate_right()

<Piece>:
    canvas.before:
        PushMatrix
        Rotate:
            angle: self.rotation
            axis: 0,0,1
            origin: self.center[0] - self.pos[0], self.center[1] - self.pos[1]
    canvas.after:
        PopMatrix
    pos_hint: {'top': 1 - (self.grid_pos_y / self.field_height), 'x': (self.grid_pos_x) / self.field_width}

<Block>:
    canvas.before:
        PushMatrix
        Rotate:
            angle: self.rotation
            axis: 0,0,1
            origin: self.center
        Scale:
            x: self.scale
            y: self.scale
            origin: self.center
    canvas:
        Color:
            rgba: root.color
        Rectangle:
            source: app.block_file(self.block_type)
            pos: self.pos
            size: self.size
        Color:
            rgba: root.color[0], root.color[1], root.color[2], root.color[3] * .333
        Rectangle:
            size: self.size
            pos: self.pos
    canvas.after:
        PopMatrix

<BGColumn>:
    canvas:
        Color:
            rgba: app.theme.background_column
        Rectangle:
            source: app.column_image
            pos: self.pos
            size: self.size

<BG>:
    canvas:
        Color:
            rgba: self.owner.bg_color
        Rectangle:
            pos: self.pos
            size: self.size

<Row>:
    pos_hint:{'y': 1 - ((self.grid_pos + 1) * self.size_hint_y)}

<PlayArea>:

<GameOver>:
    orientation: 'vertical'

<GameOverInfo>:
    text_height: self.height / 18
    opacity: 0
    orientation: 'vertical'
    Widget:
    Image:
        source: 'data/congratulations.png' if root.win else 'data/game_over.png'
        allow_stretch: True
        size_hint_y: None
        height: root.text_height * 2
    NormalLabel:
        size_hint_y: None
        height: root.text_height
        text: 'Score: '+root.score
    NormalLabel:
        size_hint_y: None
        height: root.text_height
        text: 'Game Time: '+root.length
    NormalLabel:
        size_hint_y: None
        height: root.text_height
        text: root.lines+' Lines Completed'
    NormalLabel:
        size_hint_y: None
        height: root.text_height
        text: root.pieces+' Pieces Played'
    Widget:

""")

from globals import fps, pieces, default_bg, levels, clear_modes


def draw_block(canvas, pos, size, color, block=''):
    """Draws a block on the given canvas element
    Arguments:
        canvas: canvas object to draw the block on
        pos: x, y tuple for block position
        size: width, height tuple for block size
        color: r, g, b, a tuple describing the color of the block.  Set to transparent black if block is ''
        block: string, type of block.  If '', will be drawn invisible, if 'shadow' will be drawn as a shadow (simplified).  Otherwise, must be a piece type name.
    Returns:
        Added canvas elements (Color, Rectangle in shadow mode or Color, Rectangle, Color, Rectangle in normal mode.
        Last element is a data list containing passed in data: x, y, width, height, color
    """

    app = App.get_running_app()

    x_pos, y_pos = pos
    size_x, size_y = size

    if block == 'shadow':
        col = Color(*color)
        box = Rectangle(pos=(x_pos, y_pos), size=(size_x, size_y))
        canvas.add(col)
        canvas.add(box)
        data = [x_pos, y_pos, size_x, size_y, color[-1]]
        return [col, box, data]
    else:
        if block == '':
            color_value = (0, 0, 0, 0)
            color2_value = color_value
        else:
            color_value = color[:3] + [1]
            color2_value = color[:3] + [app.piece_color2_alpha]
        color = Color(*color_value)
        box = Rectangle(pos=(x_pos, y_pos), size=(size_x, size_y), source=app.block_file(block))
        color2 = Color(*color2_value)
        box2 = Rectangle(pos=(x_pos, y_pos), size=(size_x, size_y))
        canvas.add(color)
        canvas.add(box)
        canvas.add(color2)
        canvas.add(box2)
        data = [x_pos, y_pos, size_x, size_y, 1, app.piece_color2_alpha]
        return [color, box, color2, box2, data]


class GameScreen(TetraScreen):
    show_chat = BooleanProperty(False)
    block_height = NumericProperty(0)  #Variable that indicates the current max height of the blocks in the play field
    opponent_block_height = NumericProperty(0)  #When in multiplayer mode, this indicates the block height of opponent's field
    piece_randomizer = None
    piece_seed = 0
    game_mode = StringProperty('A')  #A = Marathon, B = Sprint, C = Multiplayer
    bg_color = ListProperty([0, 0, 0, 1])
    fall_speed = 0.2
    completed_lines = NumericProperty(0)
    level = NumericProperty(0)
    game_running = BooleanProperty(False)
    screen_manager = ObjectProperty()
    field_width = NumericProperty(10)
    field_height = NumericProperty(18)
    current_piece = ObjectProperty(allownone=True)
    storing_piece = ObjectProperty(allownone=True)
    next_piece = None
    stored_piece = None
    key_press = StringProperty()
    board_overflow = []
    board_elements = []
    board = ObjectProperty()
    play_area = ObjectProperty()
    board_color = (.5, 0, 0, 1)
    score = NumericProperty(0)
    update_function = ObjectProperty(allownone=True)
    completed_rows = ListProperty()
    clearing_rows = BooleanProperty(False)
    adding_rows = BooleanProperty(False)
    lines_to_add = ListProperty()
    added_rows = ListProperty()
    adding_animation = ObjectProperty(allownone=True)
    board_widgets = ListProperty()
    level_ticks = 1
    ticks = 0
    clear_mode = ''
    clearing_animation = None
    can_store = BooleanProperty(True)
    paused = BooleanProperty(False)
    unpausing = BooleanProperty(False)
    unpausing_widget = ObjectProperty(allownone=True)
    chances = []
    level_offset = NumericProperty(0)
    level_offset_real = NumericProperty(0)
    garbage_lines = ListProperty()
    remaining_lines = NumericProperty(0)
    falling_piece = BooleanProperty(False)
    clear_line_animations = []

    periodic_add_line_counter = NumericProperty(0)
    periodic_add_line_ticks = NumericProperty(0)
    periodic_add_lines = NumericProperty(0)  #Add lines occasionally
    start_speed = NumericProperty(0)  #Starting level
    start_filled = NumericProperty(0)  #Number of lines to fill with garbage
    start_length = NumericProperty(1)  #Number of lines to clear to complete game

    replay = BooleanProperty(False)
    replay_path = StringProperty()
    replay_length = NumericProperty()

    move_delay_fast = 10
    move_delay_slow = 24
    max_move = 4
    max_move_down = 3
    max_rotate = 12
    move_speedup_fast = 5
    move_speedup_slow = 2

    total_ticks = NumericProperty(0)
    piece_ticks = 0
    history = []
    history_playback = []
    total_pieces = 0

    m_rotate_l = 0
    m_rotate_l_delay = 25
    m_rotate_r = 0
    m_rotate_r_delay = 25
    m_down = 0
    m_down_delay = 14
    m_left = 0
    m_left_delay = 14
    m_right = 0
    m_right_delay = 14

    m_drop = 0
    m_store = 0
    m_pause = 0

    playback_speed = NumericProperty(1)

    def back(self):
        app = App.get_running_app()
        if self.replay:
            app.replay('right')
        elif self.game_mode == 'A':
            app.marathon('right')
        elif self.game_mode == 'B':
            app.sprint('right')
        else:
            app.multiplayer_send('leave game', [])
            app.multiplayer('right')

    def move_x_percent(self, percent):
        if self.current_piece:
            space_l, piece_width = self.get_piece_spacing(self.current_piece.piece_grid)
            width = self.field_width - piece_width
            target_grid = int(round(width * percent)) - space_l
            if self.current_piece.grid_h > target_grid:
                if self.m_left == 0:
                    self.move_left()
                self.m_left += 1
                self.m_right = 0
            elif self.current_piece.grid_h < target_grid:
                if self.m_right == 0:
                    self.move_right()
                self.m_right += 1
                self.m_left = 0
            else:
                self.m_left = 0
                self.m_right = 0

    def move_x_percent_off(self):
        self.m_left = 0
        self.m_right = 0

    def move_down_touch(self):
        self.m_down += 1

    def move_down_touch_off(self):
        self.m_down = 0

    def move_left_touch(self):
        self.m_left += 1

    def move_left_touch_off(self):
        self.m_left = 0

    def move_right_touch(self):
        self.m_right += 1

    def move_right_touch_off(self):
        self.m_right = 0

    def add_lines(self):
        if self.lines_to_add:
            self.added_rows = self.lines_to_add
            self.lines_to_add = []

    def add_line(self):
        #add a single line to the bottom of the field
        self.adding_rows = True
        add_length = 0.025
        line_to_add = self.added_rows.pop(0)
        space, block = line_to_add
        board_data = self.board_elements
        new_line = self.spacer_line(space, block)
        self.board_elements = board_data[1:] + [new_line]
        for index, widget in enumerate(self.board_widgets):
            animation = Animation(grid_pos=widget.grid_pos-1, duration=add_length, t='out_back')
            self.clear_line_animations.append([widget, animation])
            animation.start(widget)
        self.adding_animation = Clock.schedule_once(self.add_line_finished, add_length)

    def add_line_finished(self, *_):
        self.stop_line_animations()
        self.update_board()
        self.adding_rows = False

    def get_piece_spacing(self, grid):
        #iterate through a list and determine if each column contains any True
        column_totals = []
        width = len(grid[0])
        height = len(grid)
        for index_x in range(width):
            trues = 0
            for index_y in range(height):
                if grid[index_y][index_x] is True:
                    trues += 1
            if trues > 0:
                column_totals.append(True)
            else:
                column_totals.append(False)
        space_l = 0
        for column in column_totals:
            if column is True:
                break
            space_l += 1
        space_r = 0
        for column in reversed(column_totals):
            if column is True:
                break
            space_r += 1
        piece_width = width - space_l - space_r
        return space_l, piece_width

    def add_history(self, action):
        """
        Keep a record of actions for the game, all actions are stored as: [game_tick, action]
        """

        #if action in ['F', 'D']:
        self.history.append([self.piece_ticks, action])

    def save_history(self, time_data):
        app = App.get_running_app()
        if self.game_mode == 'C':
            return
        current_time = time.strftime("%Y-%m-%d %H-%M-%S", time_data)
        current_time_internal = time.strftime("%Y,%m,%d,%H,%M", time_data)
        file_basename = 'Game '+self.game_mode+' From '+current_time
        filename = file_basename+'.txt'
        histories_folder = os.path.join(app.savefolder, 'histories')
        filepath = os.path.join(histories_folder, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        file = open(filepath, 'w')
        file.write(current_time_internal+'\n')
        file.write(str(self.total_ticks)+'\n')
        file.write(str(self.completed_lines)+'\n')
        file.write(str(self.total_pieces)+'\n')
        file.write(str(self.score)+'\n')
        file.write(self.game_mode+'\n')
        file.write(str(self.level_offset)+'\n')
        file.write(str(self.start_length)+'\n')
        file.write(self.get_garbage_data_string()+'\n')
        for line in self.history:
            file.write(str(line[0])+','+line[1]+'\n')
        file.close()

    def load_history(self, filepath):
        try:
            self.history_playback = []
            file = open(filepath, 'r')
            for index, line in enumerate(file):
                if index == 0:
                    current_time = line.strip()
                elif index == 1:
                    self.replay_length = int(line.strip())
                elif index == 2:
                    completed_lines = int(line.strip())
                elif index == 3:
                    total_pieces = int(line.strip())
                elif index == 4:
                    score = int(line.strip())
                elif index == 5:
                    self.game_mode = line.strip()
                elif index == 6:
                    self.start_speed = int(line.strip())
                elif index == 7:
                    self.start_length = int(line.strip())
                elif index == 8:
                    garbage_data = line.strip().split(',')
                    garbage_lines = []
                    for garbage_line in garbage_data:
                        if ' ' in garbage_line:
                            line_data = [int(n) for n in garbage_line.split(' ')]
                            garbage_lines.append(line_data)
                    self.garbage_lines = garbage_lines
                else:
                    history_tick, history_action = line.strip().split(',')
                    self.history_playback.append([int(history_tick), history_action])
        except:
            self.history_playback = []
        if self.history_playback:
            return True
        else:
            return False

    def history_action(self, action):
        """
        Play back a history action
        Possible actions:
            I, J, L, O, S, Z, T - Added corrosponding piece

            7 - Rotate piece left
            9 - Rotate piece right
            4 - Move piece left
            6 - Move piece right
            5 - Move piece down
            2 - Hard drop piece
            0 - Store/recall piece

            F - Piece fell on board
            D - System moves piece down

            A## - Add line with spacer at number

            W - Game won
        """

        moved = False
        if action == 'D':
            if self.current_piece:
                self.current_piece.move_down()
                moved = True
        elif action == 'F':
            if self.current_piece:
                x = self.current_piece.grid_h
                y = self.current_piece.grid_v
                grid = self.current_piece.piece_grid
                color = self.current_piece.color
                name = self.current_piece.name
                self.fall_piece(x, y, grid, color, name)
            moved = True
        elif action == '7':
            if self.current_piece:
                moved = self.current_piece.rotate_piece('l')
        elif action == '9':
            if self.current_piece:
                moved = self.current_piece.rotate_piece('r')
        elif action == '4':
            if self.current_piece:
                moved = self.current_piece.move_left()
        elif action == '6':
            if self.current_piece:
                moved = self.current_piece.move_right()
        elif action == '5':
            if self.current_piece:
                moved = self.current_piece.move_down(quick=True)
        elif action == '2':
            if self.current_piece:
                self.current_piece.hard_down()
            moved = True
        elif action == '0':
            moved = self.store()
        elif action == 'W':
            self.game_win()
            moved = True
        elif action in ['I', 'J', 'L', 'O', 'S', 'Z', 'T']:
            self.new_piece(new_ident=action)
            moved = True
        elif action.startswith('A'):
            space = int(action[1:])
            block = random.randint(0, len(pieces)-1)
            self.lines_to_add.append([space, block])
            moved = True
        else:
            moved = True
        if not moved:
            self.failed_play_recorded()

    def failed_play_recorded(self):
        app = App.get_running_app()
        self.end_game()
        app.message("Unable to\nplay replay")
        app.replay()

    def enable_show_chat(self):
        app = App.get_running_app()
        if app.connected and self.game_mode == 'C':
            self.show_chat = True

    def pause(self, force=False, silent=False):
        app = App.get_running_app()
        if not self.game_running:
            return
        if self.unpausing:
            app.pause_music()
            if not silent:
                app.multiplayer_send('pause start', [])
            self.unpause_countdown_cancel()
            self.enable_show_chat()
            return
        if self.paused and not force:
            self.show_chat = False
            Clock.schedule_once(self.refresh_piece_size, 1)
            #app.resume_music()
            if self.replay:
                self.paused = False
                self.update_function = Clock.schedule_interval(self.game_loop_playback, 1.0/fps)
            else:
                if not silent:
                    app.multiplayer_send('pause end', [])
                self.unpause_countdown_start()
        else:
            self.enable_show_chat()
            app.pause_music()
            if not silent:
                app.multiplayer_send('pause start', [])
            if not self.paused:
                app.play_sound('pause')
            self.cancel_clear_line()
            while self.completed_rows:
                self.clear_line(instant=True)
            self.paused = True
            if self.update_function:
                self.update_function.cancel()

    def unpause_countdown_start(self):
        play_area = self.ids['playArea']
        self.unpausing_widget = Countdown()
        self.unpausing_widget.bind(on_count_finished=self.unpause_countdown_finish)
        play_area.add_widget(self.unpausing_widget)
        self.unpausing = True
        self.unpausing_widget.start()

    def unpause_countdown_cancel(self):
        if self.unpausing_widget is not None:
            self.unpausing_widget.cancel()
            play_area = self.ids['playArea']
            play_area.remove_widget(self.unpausing_widget)
        self.unpausing = False
        self.unpausing_widget = None

    def refresh_piece_size(self, *_):
        if self.current_piece:
            self.current_piece.on_size()
            if self.current_piece.piece_shadow:
                self.current_piece.piece_shadow.on_size()

    def unpause_countdown_finish(self, *_):
        self.unpause_countdown_cancel()
        self.paused = False
        self.play_music()
        self.update_function = Clock.schedule_interval(self.game_loop, 1.0/fps)

    def get_garbage_data_string(self):
        garbage_data = []
        for data in self.garbage_lines:
            garbage_data.append(' '.join([str(item) for item in data]))
        garbage_string = ','.join(garbage_data)
        return garbage_string

    def save_pause(self):
        app = App.get_running_app()
        if self.game_mode == 'C':
            app.pause_data = ''
            return
        if not self.history:
            return
        if self.replay:
            return
        #save the current game state
        total_ticks = self.total_ticks
        total_pieces = self.total_pieces
        if self.current_piece:
            current_piece_type = self.current_piece.name
            current_piece_x = self.current_piece.grid_h
            current_piece_y = self.current_piece.grid_v
            current_piece_rotate = self.current_piece.rotate_index
        else:
            current_piece_type = ''
            current_piece_x = 0
            current_piece_y = 0
            current_piece_rotate = 0
        if self.stored_piece:
            stored_piece_type = self.stored_piece['name']
        else:
            stored_piece_type = ''
        next_piece = self.next_piece['name']
        history = self.history
        chances = self.chances
        score = self.score
        completed_lines = self.completed_lines
        piece_ticks = self.piece_ticks
        board_elements = self.board_elements
        board_format = []
        for row in board_elements:
            for column in row:
                if column:
                    #point = str(column[0])+' '+str(column[1])+' '+str(column[2])+' '+column[3]
                    point = column[3]
                else:
                    point = '0'
                board_format.append(point)
        add_lines_data = []
        for line in self.lines_to_add:
            add_lines_data.append(str(line[0]))
        add_lines = ','.join(add_lines_data)
        board_string = ','.join(board_format)
        garbage_string = self.get_garbage_data_string()
        pause_data = [total_ticks, total_pieces, current_piece_type, current_piece_x, current_piece_y, current_piece_rotate, stored_piece_type, next_piece, score, completed_lines, piece_ticks, board_string]
        pause_data = pause_data + [self.game_mode, self.level_offset, self.start_length, self.periodic_add_lines, self.periodic_add_line_counter, add_lines, garbage_string]
        pause_data = pause_data + chances
        history_data = []
        for line in history:
            history_data.append(str(line[0])+','+line[1])
        pause_data = pause_data + history_data
        app.pause_data = ';'.join(str(x) for x in pause_data)

    def resume_pause(self):
        app = App.get_running_app()
        pause_string = app.pause_data
        if pause_string:
            #parse pause string
            try:
                add_lines = []
                history_data = pause_string.split(';')
                total_ticks = int(history_data[0])
                total_pieces = int(history_data[1])
                current_piece_type = history_data[2]
                current_piece_x = int(history_data[3])
                current_piece_y = int(history_data[4])
                current_piece_rotate = int(history_data[5])
                stored_piece_type = history_data[6]
                next_piece = history_data[7]
                score = int(history_data[8])
                completed_lines = int(history_data[9])
                piece_ticks = int(history_data[10])
                board_string = history_data[11]
                board_format = board_string.split(',')
                game_mode = history_data[12]
                level_offset = int(history_data[13])
                start_length = int(history_data[14])
                periodic_add_lines = int(history_data[15])
                periodic_add_line_counter = int(history_data[16])
                add_line_data = history_data[17].split(',')
                for add_line in add_line_data:
                    if add_line:
                        block = random.randint(0, len(pieces)-1)
                        add_lines.append([int(add_line), block])
                garbage_data = history_data[18].split(',')
                garbage_lines = []
                for line in garbage_data:
                    if ' ' in line:
                        line_data = [int(n) for n in line.split(' ')]
                        garbage_lines.append(line_data)

                chances = [int(history_data[19]), int(history_data[20]), int(history_data[21]), int(history_data[22]), int(history_data[23]), int(history_data[24]), int(history_data[25])]
                history_list = history_data[26:]
                history = []
                for line in history_list:
                    history_ticks, history_action = line.split(',')
                    history_element = [int(history_ticks), history_action]
                    history.append(history_element)
            except:
                return False

            #prepare game to resume
            self.end_game()
            self.setup_randomizer()
            self.setup_board()
            self.game_mode = game_mode
            self.periodic_add_lines = periodic_add_lines
            self.periodic_add_line_counter = periodic_add_line_counter
            self.level_offset = level_offset
            self.start_length = start_length
            self.garbage_lines = garbage_lines
            self.total_ticks = total_ticks
            self.total_pieces = total_pieces
            self.piece_ticks = piece_ticks
            self.chances = chances
            self.history = history
            self.score = score
            self.lines_to_add = add_lines
            self.completed_lines = completed_lines
            self.level = completed_lines // 10
            index_data = 0
            for row in self.board_elements:
                for index, column in enumerate(row):
                    if board_format[index_data] == '0':
                        row[index] = None
                    else:
                        color_name = board_format[index_data]
                        try:
                            color = getattr(app.theme, color_name)
                        except:
                            color_name = 'T'
                            color = app.theme.T
                        color = color[:3] + [color_name]
                        row[index] = color
                    index_data += 1
            self.update_board()
            if current_piece_type:
                piece_data = pieces[current_piece_type]
                self.add_piece(piece_data, rotation=current_piece_rotate)
                self.current_piece.grid_pos_x = current_piece_x
                self.current_piece.grid_h = current_piece_x
                self.current_piece.start_x_pos = current_piece_x
                self.current_piece.grid_pos_y = current_piece_y
                self.current_piece.grid_v = current_piece_y
                Clock.schedule_once(self.current_piece.setup_grid)
            else:
                self.current_piece = None
            if stored_piece_type:
                self.stored_piece = pieces[stored_piece_type]
                store_area = self.ids['storedPiece']
                color = getattr(app.theme, self.stored_piece['name'])
                self.piece_to_area(store_area, self.stored_piece['shapes'][0], color, self.stored_piece['name'])
            else:
                self.stored_piece = None
            self.remaining_lines = self.start_length - self.completed_lines
            self.next_piece = pieces[next_piece]
            self.show_next_piece()
            self.game_running = True
            self.set_level_speed()
            self.update_function = Clock.schedule_interval(self.game_loop, 1.0/fps)
            self.pause()
            #self.play_music()
            return True

    def on_enter(self):
        self.show_chat = False
        app = App.get_running_app()
        app.clear_selected_overlay()
        self.ids.playLayout.refresh_positions()
        self.bg_color = default_bg

    def on_leave(self):
        self.show_chat = False
        if self.game_running:
            self.save_pause()
        self.replay = False
        self.end_game()

    def move_left(self, *_):
        if self.paused or self.falling_piece:
            return
        if self.current_piece:
            moved = self.current_piece.move_left()
            if moved:
                self.add_history('4')

    def move_right(self, *_):
        if self.paused or self.falling_piece:
            return
        if self.current_piece:
            moved = self.current_piece.move_right()
            if moved:
                self.add_history('6')

    def move_down(self, *_, instalock=False):
        if self.paused or self.falling_piece:
            return
        if self.current_piece:
            moved = self.current_piece.move_down(quick=True, instalock=instalock)
            if moved:
                self.add_history('5')

    def rotate_right(self, *_):
        if self.paused or self.falling_piece:
            return
        if self.current_piece:
            moved = self.current_piece.rotate_piece(direction='r')
            if moved:
                self.add_history('9')

    def rotate_left(self, *_):
        if self.paused or self.falling_piece:
            return
        if self.current_piece:
            moved = self.current_piece.rotate_piece(direction='l')
            if moved:
                self.add_history('7')

    def hard_down(self, safe=False, *_):
        if self.paused or self.falling_piece:
            return
        if self.current_piece:
            if safe and self.piece_ticks < 10:
                return
            self.add_history('2')
            self.current_piece.hard_down()

    def store(self):
        app = App.get_running_app()
        if self.paused or self.falling_piece:
            return
        if self.current_piece and self.can_store:
            self.can_store = False
            store_area = self.ids['storedPiece']
            current_data = self.current_piece.data
            if self.stored_piece:
                #swap stored and current
                stored_data = self.stored_piece
                self.stored_piece = current_data
                self.remove_current(fly_to=store_area)
                self.add_piece(stored_data)
            else:
                self.stored_piece = current_data
                self.remove_current(fly_to=store_area)
            color = getattr(app.theme, self.stored_piece['name'])
            self.piece_to_area(store_area, self.stored_piece['shapes'][0], color, self.stored_piece['name'])
            self.add_history('0')
            app.play_sound('store')
            self.piece_ticks = 0
            return True
        return False

    def dismiss(self):
        if not self.game_running:
            return False
        else:
            if self.paused:
                self.save_pause()
                self.back()
            else:
                self.pause()
            return True

    def key(self, key, down):
        app = App.get_running_app()
        if self.paused or self.replay or not self.game_running:
            super().key(key, down)
        if self.replay:
            self.playback_speed = 4
            return
        #if key == 96 and down:
        #    app.multiplayer_receive(self, 'add lines;1,0')
        if key in app.m_left:
            if down:
                if self.m_left == 0:
                    self.m_left = 1
                    self.move_left()
            else:
                self.m_left = 0
        elif key in app.m_right:
            if down:
                if self.m_right == 0:
                    self.m_right = 1
                    self.move_right()
            else:
                self.m_right = 0

        elif key in app.m_rotate_r:
            if down:
                if self.m_rotate_r == 0:
                    self.m_rotate_r = 1
                    self.rotate_right()
            else:
                self.m_rotate_r = 0
        elif key in app.m_rotate_l:
            if down:
                if self.m_rotate_l == 0:
                    self.m_rotate_l = 1
                    self.rotate_left()
            else:
                self.m_rotate_l = 0

        elif key in app.m_down:
            if down:
                if self.m_down == 0:
                    self.m_down = 1
                    self.move_down(instalock=True)
            else:
                self.m_down = 0

        elif key in app.m_drop:
            if down:
                if self.m_drop == 0:
                    if self.piece_ticks > 5:
                        self.m_drop = 1
                        self.hard_down()
            else:
                self.m_drop = 0

        elif key in app.m_store:
            if down:
                if self.m_store == 0:
                    self.m_store = 1
                    self.store()
            else:
                self.m_store = 0
        elif key in app.m_pause:
            if down:
                if self.m_pause == 0:
                    self.m_pause = 1
                    self.pause()
            else:
                self.m_pause = 0

    def game_loop_playback(self, *_):
        app = App.get_running_app()
        if self.paused:
            return
        for loop in range(0, self.playback_speed):
            if not self.game_running:
                break
            if self.completed_rows:
                if not self.clearing_rows:
                    if self.playback_speed > 1:
                        instant = True
                    else:
                        instant = False
                    self.clear_line(quick=not app.line_animations, instant=instant)
            elif self.added_rows:
                if not self.adding_rows:
                    self.add_line()
            elif self.falling_piece:
                return
            else:
                while self.history_playback[0][0] == self.piece_ticks:
                    current_history = self.history_playback.pop(0)
                    self.history_action(current_history[1])
                    if not self.history_playback:
                        self.game_over()
                        break
                    if current_history[1] in ['I', 'J', 'L', 'O', 'S', 'Z', 'T']:
                        self.piece_ticks += 1
                self.piece_ticks += 1
                self.total_ticks += 1
                if self.total_ticks > self.replay_length:
                    self.game_over()
        self.playback_speed = 1

    def game_loop(self, *_):
        app = App.get_running_app()
        if self.paused:
            return
        if self.completed_rows:
            if not self.clearing_rows:
                self.clear_line(quick=not app.line_animations)
        elif self.added_rows:
            if not self.adding_rows:
                self.add_line()
        elif self.falling_piece:
            return
        else:
            if self.periodic_add_lines > 0:
                self.periodic_add_line_counter += 1
                if self.periodic_add_line_counter > self.periodic_add_line_ticks:
                    self.periodic_add_line_counter = 0
                    space = random.randint(0, self.field_width - 1)
                    block = random.randint(0, len(pieces)-1)
                    self.lines_to_add.append([space, block])
                    #self.add_score('lines', 1)
                    self.add_history('A'+str(space))
            self.piece_ticks += 1
            self.total_ticks += 1
            if self.current_piece is None:
                self.ticks = 0
                self.piece_ticks = 0
                self.new_piece()
                self.piece_ticks = 1
            else:
                #Piece is in play
                #Handle drop forgiveness
                self.current_piece.drop_forgive -= 1

                #Handle controls
                if self.m_left > 0:
                    self.m_left += 1
                    if self.m_left >= self.m_left_delay:
                        self.move_left()
                        self.m_left = 1
                        self.m_left_delay -= self.move_speedup_fast
                        if self.m_left_delay < self.max_move:
                            self.m_left_delay = self.max_move
                else:
                    self.m_left_delay = self.move_delay_fast
                if self.m_right > 0:
                    self.m_right += 1
                    if self.m_right >= self.m_right_delay:
                        self.move_right()
                        self.m_right = 1
                        self.m_right_delay -= self.move_speedup_fast
                        if self.m_right_delay < self.max_move:
                            self.m_right_delay = self.max_move
                else:
                    self.m_right_delay = self.move_delay_fast
                if self.m_down > 0:
                    self.m_down += 1
                    if self.m_down >= self.m_down_delay:
                        self.move_down()
                        self.ticks = 0
                        self.m_down = 1
                        self.m_down_delay -= self.move_speedup_fast
                        if self.m_down_delay < self.max_move_down:
                            self.m_down_delay = self.max_move_down
                else:
                    self.m_down_delay = self.move_delay_fast
                if self.m_rotate_l > 0:
                    self.m_rotate_l += 1
                    if self.m_rotate_l >= self.m_rotate_l_delay:
                        self.rotate_left()
                        self.m_rotate_l = 1
                        self.m_rotate_l_delay -= self.move_speedup_fast
                        if self.m_rotate_l_delay < self.max_rotate:
                            self.m_rotate_l_delay = self.max_rotate
                else:
                    self.m_rotate_l_delay = self.move_delay_slow
                if self.m_rotate_r > 0:
                    self.m_rotate_r += 1
                    if self.m_rotate_r >= self.m_rotate_r_delay:
                        self.rotate_right()
                        self.m_rotate_r = 1
                        self.m_rotate_r_delay -= self.move_speedup_fast
                        if self.m_rotate_r_delay < self.max_rotate:
                            self.m_rotate_r_delay = self.max_rotate
                else:
                    self.m_rotate_r_delay = self.move_delay_slow

                #Handle auto-fall
                self.ticks += 1
                if self.ticks >= self.level_ticks:
                    self.add_history('D')
                    self.current_piece.move_down()
                    self.ticks = 0

    def toggle_game(self):
        if not self.game_running:
            self.start_game()
        else:
            app = App.get_running_app()
            self.show_chat = True
            self.end_game()
            app.pause_data = ''
            self.history = []

    def setup_randomizer(self, seed=None):
        self.piece_randomizer = random.Random()
        if seed is None:
            self.piece_seed = generate_seed()
        else:
            self.piece_seed = seed
        self.piece_randomizer.seed(self.piece_seed)

    def start_game(self, playback=False, seed=None):
        app = App.get_running_app()
        self.end_game()
        self.setup_randomizer(seed)
        self.setup_board()
        self.game_running = True
        self.remaining_lines = self.start_length
        if playback:
            loaded = self.load_history(self.replay_path)
            if not loaded:
                self.failed_play_recorded()
                return
            self.level_offset = self.start_speed
            self.set_level_speed()
            if self.game_mode == 'B':
                self.fill_garbage_lines()
                self.update_board()
            self.update_function = Clock.schedule_interval(self.game_loop_playback, 1.0/fps)
        else:
            self.level_offset = self.start_speed
            self.set_level_speed()
            self.garbage_lines = []
            for index in range(self.start_filled * 2):
                self.garbage_lines.append(self.random_line())
            self.fill_garbage_lines()
            self.update_board()

            app.play_sound('new_game')
            self.paused = True
            self.unpause_countdown_start()
            #self.update_function = Clock.schedule_interval(self.game_loop, 1.0/fps)

    def play_music(self, *_):
        app = App.get_running_app()
        if app.screen_manager.current != 'game':
            return
        if not self.game_running:
            return
        app.start_music()
        if self.paused and not self.unpausing:
            return
        app.resume_music()

    def end_game(self):
        app = App.get_running_app()
        if self.game_running:
            app.multiplayer_send('game over', [])
        app.stop_music()
        self.opponent_block_height = 0
        self.block_height = 0
        self.playback_speed = 1
        self.falling_piece = False
        self.periodic_add_line_counter = 0
        self.level_offset = 0
        self.bg_color = default_bg
        self.cancel_clear_line()
        self.adding_rows = False
        self.lines_to_add = []
        self.added_rows = []
        self.board_overflow = []
        self.score = 0
        self.level = 0
        self.completed_lines = 0
        self.game_running = False
        self.paused = False
        self.unpause_countdown_cancel()
        if self.update_function:
            self.update_function.cancel()
        if self.play_area:
            self.play_area.clear_widgets()
        self.next_piece = None
        self.stored_piece = None
        self.ids['storedPiece'].canvas.clear()
        self.ids['nextPiece'].canvas.clear()
        if self.current_piece:
            self.current_piece.piece_shadow = None
        self.current_piece = None

        self.m_rotate_l = 0
        self.m_rotate_r = 0
        self.m_down = 0
        self.m_left = 0
        self.m_right = 0
        self.m_drop = 0
        self.m_store = 0
        self.m_pause = 0

        self.piece_ticks = 0
        self.total_ticks = 0
        self.history = []
        self.can_store = True
        self.ticks = 0
        self.set_level_speed()
        self.completed_rows = []
        self.clearing_rows = False
        self.chances = [1, 1, 1, 1, 1, 1, 1]
        self.total_pieces = 0

    def game_win(self):
        self.enable_show_chat()
        app = App.get_running_app()
        if self.paused:
            if self.unpausing:
                self.unpause_countdown_cancel()
            self.paused = False
        self.piece_ticks = 1
        app.stop_music()
        self.add_history('W')
        app.play_sound('game_win')
        self.game_running = False
        if self.update_function:
            self.update_function.cancel()
        app.pause_data = ''
        if not self.replay:
            time_data = time.localtime()
            self.save_history(time_data)
            date_data = time.strftime("%b %e, %Y (%I:%M%p)", time_data)
            app.add_score(self.score, self.completed_lines, date_data, self.game_mode)
        self.history = []
        play_area = self.ids['playArea']
        game_over_widget = GameOver()
        play_area.add_widget(game_over_widget)
        game_over_widget.start(self.field_height)
        length_formatted = time_index(self.total_ticks/fps)
        game_over_info = GameOverInfo(length=length_formatted, lines=str(self.completed_lines), score=str(self.score), pieces=str(self.total_pieces))
        animation = Animation(duration=.5) + Animation(opacity=1, duration=1)
        animation.start(game_over_info)
        play_area.add_widget(game_over_info)
        self.remove_current()

    def game_over(self):
        self.enable_show_chat()
        app = App.get_running_app()
        if self.paused:
            if self.unpausing:
                self.unpause_countdown_cancel()
            self.paused = False
        app.multiplayer_send('game over', [])
        app.stop_music()
        app.play_sound('game_over')
        self.game_running = False
        self.update_function.cancel()
        self.lines_to_add = []
        app.pause_data = ''
        if not self.replay and self.game_mode != 'B':
            time_data = time.localtime()
            self.save_history(time_data)
            date_data = time.strftime("%b %e, %Y (%I:%M%p)", time_data)
            app.add_score(self.score, self.completed_lines, date_data, self.game_mode)
        self.history = []

        play_area = self.ids['playArea']
        game_over_widget = GameOver()
        play_area.add_widget(game_over_widget)

        length_formatted = time_index(self.total_ticks/fps)
        game_over_info = GameOverInfo(win=False, length=length_formatted, lines=str(self.completed_lines), score=str(self.score), pieces=str(self.total_pieces))
        animation = Animation(duration=.5) + Animation(opacity=1, duration=1)
        animation.start(game_over_info)
        play_area.add_widget(game_over_info)

        game_over_widget.start(self.field_height)
        self.remove_current()

    def fill_garbage_lines(self):
        app = App.get_running_app()
        pieces_types = list(pieces.items())
        for index_y, line in enumerate(self.garbage_lines):
            for index_x, block in enumerate(line):
                if block != 0:
                    block_style = pieces_types[block - 1][1]
                    name = block_style['name']
                    color = getattr(app.theme, name)
                    self.board_elements[self.field_height - index_y - 1][index_x] = color[:3] + [name]

    def spacer_line(self, space, block):
        app = App.get_running_app()
        width = self.field_width
        piece_key = list(pieces.keys())[block]
        piece_data = pieces[piece_key]
        block_data = getattr(app.theme, piece_data['name'])
        block_data[-1] = piece_data['name']
        line = []
        for index in range(width):
            if index == space:
                line.append(None)
            else:
                line.append(block_data)
        return line

    def random_line(self):
        width = self.field_width
        total_blocks = random.randint(3, width - 3)
        line = []
        for index in range(width):
            if index < total_blocks:
                line.append(random.randint(1, len(pieces)))
            else:
                line.append(0)
        random.shuffle(line)
        return line

    def piece_to_area(self, area, shape, color, block_type):
        area.set_piece(shape, color, block_type)

    def check_position(self, x, y, grid):
        board_data = self.board_elements
        for index_y, row in enumerate(grid):
            for index_x, column in enumerate(row):
                if column:
                    new_y = y+index_y
                    if new_y >= self.field_height:
                        #Point is below the board vertically, immediate fail
                        return False
                    new_x = x+index_x
                    if new_x < 0 or new_x >= self.field_width:
                        #Point is outside of the board horizontally, immediate fail
                        return False
                    if new_y >= 0:
                        #Point is on the board, check it normally
                        check_row = board_data[new_y]
                        check_column = check_row[new_x]
                        if check_column is not None:
                            #A block is already filled at this spot
                            return False
        return True

    def full_down(self, x, y, grid):
        y += 1
        while self.check_position(x, y, grid):
            y += 1
        return y - 1

    def remove_current(self, fly_to=None):
        if not self.current_piece:
            return
        self.current_piece.stop_animations()
        self.play_area.remove_widget(self.current_piece.piece_shadow)
        #self.current_piece.piece_shadow = None  #Causing crash on android??
        if fly_to:
            self.storing_piece = self.current_piece
            play_layout = self.ids['playLayout']
            piece_coords = self.current_piece.to_window(*self.current_piece.pos)
            size = self.current_piece.size
            self.play_area.remove_widget(self.current_piece)
            play_layout.add_widget(self.current_piece)
            self.storing_piece.size_hint = (None, None)
            self.storing_piece.size = size
            self.storing_piece.pos_hint = {}
            self.storing_piece.pos = piece_coords
            fly_to_offset_x = (fly_to.width - self.storing_piece.width) / 2
            fly_to_offset_y = (fly_to.height - self.storing_piece.height) / 2
            fly_coords = (fly_to.pos[0] + fly_to_offset_x, fly_to.pos[1] + fly_to_offset_y)
            animation = Animation(x=fly_coords[0], y=fly_coords[1], opacity=0, duration=0.25)
            animation.bind(on_complete=lambda x, y: play_layout.remove_widget(self.storing_piece))
            animation.start(self.storing_piece)
        else:
            self.play_area.remove_widget(self.current_piece)
        self.current_piece = None

    def fall_piece(self, x, y, grid, color, name, log=True, wait=False):
        if wait:
            self.falling_piece = True
            Clock.schedule_once(lambda z: self.fall_piece_finish(x, y, grid, color, name, log, sound=True), .1)
        else:
            self.fall_piece_finish(x, y, grid, color, name, log)

    def fall_piece_finish(self, x, y, grid, color, name, log, sound=False):
        app = App.get_running_app()
        self.falling_piece = False
        self.board_overflow = []
        max_overflow = 0
        piece_x_pos = None
        game_over = False
        for index_y, row in enumerate(grid):
            for index_x, column in enumerate(row):
                if column:
                    point_x = x + index_x
                    if piece_x_pos is None:
                        piece_x_pos = point_x
                    point_y = y + index_y
                    if point_y < 0:
                        overflow = 0 - point_y
                        if overflow > max_overflow:
                            max_overflow = overflow
                        if not self.board_overflow:
                            self.board_overflow = generate_2d_array(self.field_width, 4, None)
                        self.board_overflow[point_y + 4][point_x] = color[:3] + [name]
                        game_over = True
                    else:
                        self.board_elements[point_y][point_x] = color[:3] + [name]
        lines = self.clear_lines(piece_x_pos)
        if lines >= max_overflow:
            self.board_overflow = self.board_overflow[-lines:]
            game_over = False
        if not game_over:
            self.add_lines()
        if log:
            self.add_history('F')
        if sound:
            if self.current_piece:
                if self.current_piece.fall_sound:
                    app.play_sound('fall')
        self.remove_current()
        self.piece_ticks = 0
        self.update_board()
        if game_over:
            self.game_over()

    def clear_lines(self, piece_x_pos):
        app = App.get_running_app()
        self.clear_mode = random.choice(clear_modes)
        board_data = self.board_elements
        total_lines = 0
        for index, row in enumerate(board_data):
            completed = all(column is not None for column in row)
            if completed:
                total_lines += 1
                self.completed_rows.append(index)
        if total_lines:
            self.add_score('lines', total_lines)
            multiplayer_lines = total_lines - 1
            if multiplayer_lines > 0 and self.game_mode == 'C':
                lines_to_add_amount = len(self.lines_to_add)
                if lines_to_add_amount > multiplayer_lines:
                    self.lines_to_add = self.lines_to_add[multiplayer_lines:]
                elif lines_to_add_amount == multiplayer_lines:
                    self.lines_to_add = []
                else:
                    multiplayer_lines = multiplayer_lines - lines_to_add_amount
                    self.lines_to_add = []
                    app.multiplayer_send('add lines', [multiplayer_lines, piece_x_pos])
        return total_lines

    def add_score(self, trigger, amount):
        if trigger == 'lines':
            multipliers = [40, 100, 300, 1200]
            multiplier = multipliers[amount - 1]
            self.score = self.score + (multiplier * (self.level + 1))
        elif trigger == 'down':
            self.score = self.score + 1
        elif trigger == 'drop':
            self.score = self.score + amount

    def set_level_speed(self):
        if self.periodic_add_lines > 0:
            line_seconds_amounts = [0, 45, 30, 20, 10, 7.5, 5]
            line_seconds = line_seconds_amounts[self.periodic_add_lines]
            self.periodic_add_line_ticks = int(round(line_seconds * fps))
        else:
            self.periodic_add_line_ticks = 0
        try:
            if self.level_offset > self.level:
                self.level_offset_real = self.level_offset - self.level
            else:
                self.level_offset_real = 0
            level_speed = levels[self.level + self.level_offset_real]
        except:
            level_speed = levels[-1]
        self.level_ticks = int(round(level_speed * fps))
        if self.level_ticks < 1:
            self.level_ticks = 1
        self.fall_speed = level_speed

    def bg_random(self):
        return random.random() * 0.5

    def set_bg_color(self, color=None):
        if color is None:
            color = [self.bg_random(), self.bg_random(), self.bg_random(), 1]
        self.bg_color = color

    def clear_line(self, clear_mode='', instant=False, quick=False):
        app = App.get_running_app()
        animation_mode = random.choice(Block.modes)
        if len(self.completed_rows) == 4:
            app.play_sound('max_lines')
        else:
            app.play_sound('line')
        if not clear_mode:
            clear_mode = self.clear_mode
        self.completed_lines += len(self.completed_rows)
        remaining_lines = self.start_length - self.completed_lines
        if remaining_lines < 0:
            remaining_lines = 0
        self.remaining_lines = remaining_lines
        new_level = self.completed_lines // 10
        if new_level != self.level:
            Clock.schedule_once(lambda x: app.play_sound('level'), 0.5)
            self.level = new_level
            self.set_bg_color()
        self.set_level_speed()
        clear_length = app.clear_length
        fall_length = app.fall_length

        self.clearing_rows = True
        lines = []
        for row_number in sorted(self.completed_rows, reverse=True):
            self.board_elements.pop(row_number)
            lines.append(self.board_widgets[row_number])
        if instant:
            self.clear_line_finished()
        else:
            #Clear Lines
            if quick:
                animation = Animation(opacity=0, duration=clear_length)
                for line in lines:
                    animation.start(line)
            else:
                box_animation_length = clear_length/self.field_width
                for line in lines:
                    line.clear_line(clear_mode, box_animation_length, animation_mode)

            #Fall lines
            if not quick:
                for index, widget in enumerate(self.board_widgets):
                    if index < min(self.completed_rows):
                        animation = Animation(duration=clear_length) + Animation(grid_pos=widget.grid_pos+len(self.completed_rows), duration=fall_length, t='out_back')
                        self.clear_line_animations.append([widget, animation])
                        animation.start(widget)
            self.clearing_animation = Clock.schedule_once(self.clear_line_finished, clear_length+fall_length)

    def cancel_clear_line(self):
        if self.clearing_animation is not None:
            #ensure that previous animation is not going
            self.clearing_animation.cancel()
            self.clear_line_finished()

    def stop_line_animations(self):
        while self.clear_line_animations:
            data = self.clear_line_animations.pop(0)
            try:
                widget, animation = data
                animation.stop(widget)
            except:
                pass

    def clear_line_finished(self, *_):
        app = App.get_running_app()
        self.stop_line_animations()
        while len(self.board_elements) < self.field_height:
            self.board_elements.insert(0, [None] * self.field_width)
        self.completed_rows = []
        self.clearing_rows = False
        self.clearing_animation = None
        app.play_sound('line_fall')
        if self.game_mode == 'B':
            if self.completed_lines >= self.start_length:
                self.game_win()
        if not self.completed_rows:
            if self.board_overflow:
                for row_index, row in enumerate(self.board_overflow):
                    for column_index, column in enumerate(row):
                        self.board_elements[row_index][column_index] = column
        self.update_board()

    def show_next_piece(self):
        if self.next_piece:
            app = App.get_running_app()
            next_piece_area = self.ids['nextPiece']
            next_shape = self.next_piece['shapes'][0]
            next_color = getattr(app.theme, self.next_piece['name'])
            next_type = self.next_piece['name']
            self.piece_to_area(next_piece_area, next_shape, next_color, next_type)

    def get_piece(self):
        #Uses weighted random/gambler's fallacy to get the next piece

        piece_names = ['I', 'J', 'L', 'O', 'S', 'Z', 'T']
        possibilities = []
        for index, chance in enumerate(self.chances):
            for x in range(0, chance):
                possibilities.append(piece_names[index])
        piece_id = self.piece_randomizer.choice(possibilities)
        for index, piece in enumerate(piece_names):
            if piece_id == piece:
                self.chances[index] = 1
            else:
                self.chances[index] += 1
        #piece_id = random.choice(piece_names)
        piece_data = pieces[piece_id]
        return piece_data

    def new_piece(self, new_ident=None):
        self.m_down = 0
        self.m_down_delay = self.move_delay_fast
        if new_ident is None:
            if not self.next_piece:
                self.next_piece = self.get_piece()
            piece_data = self.next_piece
            ident = piece_data['name']
            self.next_piece = self.get_piece()
        else:
            ident = new_ident
            piece_data = pieces[ident]
        self.show_next_piece()
        self.add_piece(piece_data)
        self.can_store = True
        self.total_pieces += 1
        self.add_history(ident)

    def add_piece(self, piece_data, rotation=None):
        app = App.get_running_app()
        shapes = piece_data['shapes']
        shape = shapes[0]
        grid_h = int(self.field_width / 2) - round(len(shape[0]) / 2)
        offset = piece_data['offset']
        grid_v = 0 - offset
        color = getattr(app.theme, piece_data['name'])
        piece = Piece(owner=self, name=piece_data['name'], color=color[:3]+[1], board=self.board)
        piece.data = piece_data
        piece_shadow = Piece(owner=self, name=piece_data['name'], color=app.theme.shadow_color, shadow=True, board=self.board)
        piece_shadow.grid_pos_x = grid_h
        piece_shadow.grid_pos_y = grid_v
        piece.piece_shadow = piece_shadow
        piece.rotations = shapes
        piece.grid_pos_x = grid_h
        piece.grid_pos_y = grid_v
        piece.grid_v = grid_v
        piece.field_width = self.field_width
        piece.field_height = self.field_height
        if rotation is not None:
            piece.rotate_index = rotation
            rotate_grid = piece.rotations[rotation]
            piece.piece_grid = rotate_grid
        else:
            piece.rotate_index = 0
            piece.piece_grid = shape
        piece.grid_h = grid_h
        piece.start_x_pos = grid_h
        self.play_area.add_widget(piece)
        self.play_area.add_widget(piece_shadow)
        self.current_piece = piece
        self.current_piece.reset_drop()
        self.ticks = self.level_ticks

    def setup_board(self):
        self.play_area = self.ids['playArea']
        self.board_elements = generate_2d_array(self.field_width, self.field_height, None)
        self.board = RelativeLayout()
        self.play_area.clear_widgets()
        bg_color = BG(owner=self)
        self.play_area.add_widget(bg_color)
        bg = BoxLayout(orientation='horizontal')
        for row in self.board_elements[0]:
            bg.add_widget(BGColumn())
        self.play_area.add_widget(bg)
        self.play_area.add_widget(self.board)
        #self.board.bind(size=self.update_board)
        self.update_board(full=True)

    def update_board(self, full=False):
        max_height = 0
        if full:
            self.board_widgets = []
            self.board.clear_widgets()
            size_hint_y = 1 / self.field_height
            for index_y, row in enumerate(self.board_elements):
                row_widget = Row(size_hint=(1, size_hint_y), grid_pos=index_y)
                self.board_widgets.append(row_widget)
                if any(row):
                    max_height = max(max_height, self.field_height-index_y)
                row_widget.row_data = row
                row_widget.set_row()
                self.board.add_widget(row_widget)
        else:
            self.board_widgets = []
            for index_y, row in enumerate(self.board_elements):
                row_widget = self.board.children[index_y]
                row_widget.grid_pos = index_y
                row_widget.opacity = 1
                self.board_widgets.append(row_widget)
                if any(row):
                    max_height = max(max_height, self.field_height-index_y)
                row_widget.row_data = row
                if row_widget.clearing:
                    #after animating clearing on some devices, blocks may not refresh properly, so do a full redraw on them
                    row_widget.clearing = False
                    row_widget.set_row(full=True)
                else:
                    row_widget.update_row()
        self.block_height = max_height
        app = App.get_running_app()
        app.multiplayer_send('line height', [max_height])


class PlayArea(RelativeLayout):
    """Play field, holds the rows, and various other information widgets"""
    paused = BooleanProperty()
    animation = ObjectProperty(allownone=True)
    pause_opacity = NumericProperty(0)

    def on_paused(self, *_):
        if self.animation:
            self.animation.cancel(self)
        if self.paused:
            opacity = 0
        else:
            opacity = 1
        self.animation = Animation(pause_opacity=opacity, duration=.333)
        self.animation.start(self)


class PieceDisplay(RelativeLayout):
    """Shows a tetris block"""

    piece_elements = ListProperty()

    def on_size(self, *_):
        self.resize_piece()

    def resize_piece(self):
        if not self.piece_elements:
            return
        grid_x = len(self.piece_elements[0])
        grid_y = len(self.piece_elements)
        padding = self.width / (grid_x + 2)
        size_x = (self.width - padding - padding) / grid_x
        size_y = (self.height - padding - padding) / grid_y
        height = size_y * grid_y
        for index_y, row in enumerate(self.piece_elements):
            for index_x, column in enumerate(row):
                x_pos = padding + (index_x * size_x)
                y_pos = padding + (height - ((index_y + 1) * size_y))
                if column:
                    box = column[1]
                    box2 = column[3]
                    box.size = (size_x, size_y)
                    box.pos = (x_pos, y_pos)
                    box2.size = (size_x, size_y)
                    box2.pos = (x_pos, y_pos)

    def set_piece(self, piece_grid, color, block_type):
        self.piece_elements = []
        self.canvas.clear()
        for index_y, row in enumerate(piece_grid):
            row_elements = []
            for index_x, column in enumerate(row):
                if column:
                    element = draw_block(self.canvas, (0, 0), (1, 1), color, block=block_type)
                else:
                    element = None
                row_elements.append(element)
            self.piece_elements.append(row_elements)
        self.resize_piece()


class Row(RelativeLayout):
    """Displays a row of blocks.  Can also animate the blocks in various ways."""

    grid_pos = NumericProperty(0)
    elements = ListProperty()
    row_data = None
    clearing = BooleanProperty(False)
    animations = []

    def stop_animate(self):
        while self.animations:
            animation = self.animations.pop(0)
            animation.stop(self)
            animation = None

    def animate_out(self, duration, mode=None):
        app = App.get_running_app()
        self.stop_animate()
        self.animations = []

        def opacity_animate(col, col2, d, dur):
            anim = Animation(duration=d)
            anim += Animation(a=0, duration=dur)
            anim.start(col)
            anim2 = Animation(duration=d)
            anim2 += Animation(a=0, duration=dur)
            anim2.start(col2)
            self.animations.append(anim)
            self.animations.append(anim2)

        for index, element in enumerate(self.elements):
            color, box, color2, box2, original_data = element
            delay = duration * index
            pos_x, pos_y = box.pos
            if mode is None:
                pass
            if mode == 'explode':
                xvect = pos_x + ((random.random() - 0.5) * app.button_scale * 5)
                yvect = pos_y + ((random.random() - 0.5) * app.button_scale * 5)
                animation = Animation(duration=delay)
                animation += Animation(pos=(xvect, yvect), size=(0, 0), duration=duration * 3)
                animation.start(box)
                animation.start(box2)
                self.animations.append(animation)
                opacity_animate(color, color2, delay, duration * 3)
            elif mode == 'expand':
                size_x = box.size[0] * 3
                size_y = box.size[1] * 3
                pos_x = box.pos[0] - (size_x / 3)
                pos_y = box.pos[1] - (size_y / 3)
                animation = Animation(duration=delay)
                animation += Animation(pos=(pos_x, pos_y), size=(size_x, size_y), duration=duration * 2)
                animation.start(box)
                animation.start(box2)
                self.animations.append(animation)
                opacity_animate(color, color2, delay, duration * 2)
            elif mode == 'fall':
                pos_x = box.pos[0]
                pos_y = box.pos[1] - app.button_scale
                animation = Animation(duration=delay)
                animation += Animation(pos=(pos_x, pos_y), duration=duration * 2)
                animation.start(box)
                animation.start(box2)
                self.animations.append(animation)
                opacity_animate(color, color2, delay, duration * 2)
            elif mode == 'fall2':
                size_x = box.size[0]
                size_y = box.size[1] * 4
                pos_x = box.pos[0]
                pos_y = box.pos[1] - (box.size[1] * 3)
                animation = Animation(duration=delay)
                animation += Animation(pos=(pos_x, pos_y), size=(size_x, size_y), duration=duration * 2)
                animation.start(box)
                animation.start(box2)
                self.animations.append(animation)
                opacity_animate(color, color2, delay, duration * 2)
            elif mode == 'squish':
                size_x = box.size[0]
                size_y = 0
                animation = Animation(duration=delay)
                animation += Animation(size=(size_x, size_y), duration=duration * 2)
                animation.start(box)
                animation.start(box2)
                self.animations.append(animation)
                opacity_animate(color, color2, delay, duration * 2)
            else:
                opacity_animate(color, color2, delay, duration * 2)

    def on_size(self, *_):
        self.update_row()

    def set_row(self, full=True):
        app = App.get_running_app()
        if self.row_data is None:
            return
        else:
            row = self.row_data
        size_y = self.height
        size_x = self.width / len(row)
        if full:
            canvas = self.canvas
            canvas.clear()
            self.elements = []
            for index_x, column in enumerate(row):
                x_pos = index_x * size_x
                y_pos = 0
                if column is not None:
                    element = draw_block(canvas, (x_pos, y_pos), (size_x, size_y), column[:3], block=column[3])
                else:
                    element = draw_block(canvas, (x_pos, y_pos), (size_x, size_y), (0, 0, 0, 0), block='')
                self.elements.append(element)
        else:
            canvas_index = 0
            for index_x, column in enumerate(row):
                x_pos = index_x * size_x
                y_pos = 0
                color, box, color2, box2, original_data = self.elements[canvas_index]
                box.size = (size_x, size_y)
                box.pos = (x_pos, y_pos)
                box2.size = (size_x, size_y)
                box2.pos = (x_pos, y_pos)
                if column is not None:
                    color_value = column[:3] + [1]
                    color2_value = column[:3] + [app.piece_color2_alpha]
                    color.rgba = color_value
                    color2.rgba = color2_value
                    new_source = app.block_file(column[3])
                    if box.source != new_source:
                        box.source = new_source
                else:
                    color.rgba = [0, 0, 0, 0]
                    color2.rgba = [0, 0, 0, 0]
                    new_source = app.block_file('')
                    if box.source != new_source:
                        box.source = new_source
                canvas_index += 1

    def update_row(self, *_):
        self.set_row(full=False)

    def clear_line(self, clear_mode, box_animation_length, animation_mode):
        self.clearing = True
        boxes = self.elements
        if clear_mode == 'normal':
            boxes.reverse()
        elif clear_mode == 'random':
            random.shuffle(boxes)
        elif clear_mode in ['inward', 'outward']:
            midpoint = len(boxes) // 2
            boxes_r = boxes[:midpoint]
            boxes_l = boxes[midpoint:]
            if clear_mode == 'inward':
                boxes_l.reverse()
            else:
                boxes_r.reverse()
            boxes = []
            for index, box in enumerate(boxes_l):
                boxes.append(box)
                boxes.append(boxes_r[index])
        self.animate_out(box_animation_length, animation_mode)


class Piece(RelativeLayout):
    """Widget that displays and handles the logic of a single moving piece"""

    start_x_pos = NumericProperty(1)
    owner = ObjectProperty()
    board = ObjectProperty()
    name = StringProperty()
    data = None
    color = ListProperty()
    field_width = NumericProperty(10)
    field_height = NumericProperty(18)
    grid_h = NumericProperty(1)
    grid_v = NumericProperty(1)
    grid_pos_x = NumericProperty(1)
    grid_pos_y = NumericProperty(1)
    piece_grid = ListProperty()
    rotation = NumericProperty(0)
    rotations = ListProperty()
    rotate_index = NumericProperty(0)
    animate_x = ObjectProperty(allownone=True)
    animate_y = ObjectProperty(allownone=True)
    animate_rotate = ObjectProperty(allownone=True)
    quick_fall = BooleanProperty(False)
    down_y = NumericProperty(0)
    piece_shadow = ObjectProperty(allownone=True)
    shadow = BooleanProperty(False)
    drop_forgive = NumericProperty(0)
    fall_sound = BooleanProperty(True)
    canvas_blocks = ListProperty()

    def reset_drop(self):
        app = App.get_running_app()
        self.drop_forgive = fps * app.drop_forgive_multiplier

    def on_size(self, *_):
        if self.piece_grid:
            self.setup_grid()

    def stop_animations(self):
        self.stop_animate_x()
        self.stop_animate_y()
        self.stop_animate_rotate()
        if self.piece_shadow:
            self.piece_shadow.stop_animations()

    def stop_animate_y(self):
        try:
            self.animate_y.stop(self)
        except:
            pass

    def stop_animate_x(self):
        try:
            self.animate_x.stop(self)
        except:
            pass

    def stop_animate_rotate(self):
        try:
            self.animate_rotate.stop(self)
        except:
            pass

    def on_piece_grid(self, *_):
        self.setup_grid()

    def move_left(self):
        app = App.get_running_app()
        x = self.grid_h - 1
        y = self.grid_v
        can_move = self.owner.check_position(x, y, self.piece_grid)
        if can_move:
            app.play_sound('move')
            self.grid_h = x
            return True
        else:
            app.play_sound('wall')
        return False

    def move_right(self):
        app = App.get_running_app()
        x = self.grid_h + 1
        y = self.grid_v
        can_move = self.owner.check_position(x, y, self.piece_grid)
        if can_move:
            app.play_sound('move')
            self.grid_h = x
            return True
        else:
            app.play_sound('wall')
        return False

    def move_down(self, fall=True, quick=False, instalock=False):
        app = App.get_running_app()
        x = self.grid_h
        y = self.grid_v + 1
        can_move = self.owner.check_position(x, y, self.piece_grid)
        can_move_start = self.owner.check_position(self.start_x_pos, y, self.piece_grid)
        if can_move:
            self.fall_sound = True
            self.start_x_pos = self.grid_h
            self.reset_drop()
            if quick:
                self.owner.add_score('down', 1)
                self.quick_fall = True
            self.grid_v = y
            return True
        elif can_move_start:
            self.start_x_pos = x
            self.reset_drop()
        elif fall:
            if self.fall_sound:
                self.fall_sound = False
                app.play_sound('fall')
            if quick:
                self.drop_forgive -= 10
            else:
                self.drop_forgive -= 1
            if self.drop_forgive < 0 or instalock:
                if self.grid_pos_y < self.grid_v and app.piece_animations:
                    #special concession for the piece not appearing to be fully down
                    self.stop_animate_y()
                    self.grid_pos_y = self.grid_v
                else:
                    app.play_sound('lock')
                    self.owner.fall_piece(self.grid_h, self.grid_v, self.piece_grid, self.color, self.name)
        return False

    def hard_down(self):
        down_y = self.owner.full_down(self.grid_h, self.grid_v, self.piece_grid)
        down_amount = down_y - self.grid_v
        self.owner.add_score('drop', down_amount)
        self.quick_fall = True
        self.grid_v = down_y
        self.owner.fall_piece(self.grid_h, self.grid_v, self.piece_grid, self.color, self.name, log=False, wait=True)

    def set_rotation(self, rotate_index):
        self.rotate_index = rotate_index
        rotate_grid = self.rotations[rotate_index]
        self.piece_grid = rotate_grid
        self.update_down_y()

    def rotate_piece(self, direction='r'):
        app = App.get_running_app()
        if direction == 'r':
            rotate_index = self.rotate_index + 1
            if rotate_index >= len(self.rotations):
                rotate_index = 0
        else:
            rotate_index = self.rotate_index - 1
            if rotate_index < 0:
                rotate_index = len(self.rotations) - 1

        rotated_grid = self.rotations[rotate_index]

        new_h = self.grid_h
        new_v = self.grid_v

        can_move = self.owner.check_position(new_h, new_v, rotated_grid)
        if can_move:
            self.piece_grid = rotated_grid
            self.grid_h = new_h
            self.start_x_pos = new_h
            self.grid_v = new_v
            self.rotate_index = rotate_index
            self.stop_animate_rotate()
            if app.piece_animations and self.owner.playback_speed == 1:
                if direction == 'r':
                    self.rotation = 90
                else:
                    self.rotation = -90
                if not self.animate_rotate:
                    self.animate_rotate = Animation(rotation=0, duration=0.05)
                self.animate_rotate.start(self)
            self.update_down_y()
            app.play_sound('rotate')
            return True
        else:
            app.play_sound('rotate_fail')
        return False

    def on_grid_h(self, *_):
        app = App.get_running_app()
        try:
            self.animate_x.stop(self)
        except:
            pass
        self.stop_animate_x()
        if app.piece_animations and self.owner.playback_speed == 1:
            self.animate_x = Animation(grid_pos_x=self.grid_h, duration=0.05)
            self.animate_x.start(self)
        else:
            self.grid_pos_x = self.grid_h
        if not self.shadow:
            self.update_down_y()

    def update_down_y(self):
        if self.piece_grid:
            self.down_y = self.owner.full_down(self.grid_h, self.grid_v, self.piece_grid)
            if self.piece_shadow:
                self.piece_shadow.grid_v = self.down_y
                self.piece_shadow.grid_h = self.grid_h
                self.piece_shadow.piece_grid = self.piece_grid

    def on_grid_v(self, *_):
        app = App.get_running_app()
        if self.shadow:
            self.grid_pos_y = self.grid_v
        else:
            try:
                self.animate_y.stop(self)
            except:
                pass
            if self.quick_fall:
                self.quick_fall = False
                fall_speed = 0.05
            else:
                fall_speed = self.owner.fall_speed
            self.stop_animate_y()
            if app.piece_animations and fall_speed > (1 / fps) and self.owner.playback_speed == 1:
                self.animate_y = Animation(grid_pos_y=self.grid_v, duration=fall_speed)
                self.animate_y.start(self)
            else:
                self.grid_pos_y = self.grid_v

    def setup_grid(self, *_):
        app = App.get_running_app()
        if self.parent is None:
            return
        if self.width == 0:
            #why does this happen?? when it does, it breaks the redraw until a new grid is set
            return
        board_width = self.field_width
        board_height = self.field_height

        grid_x = len(self.piece_grid[0])
        grid_y = len(self.piece_grid)
        self.size_hint = (grid_x / board_width, grid_y / board_height)

        size_x = self.board.width / self.field_width
        size_y = self.board.height / self.field_height

        height = size_y * grid_y

        self.canvas.clear()
        for index_y, row in enumerate(self.piece_grid):
            for index_x, column in enumerate(row):
                x_pos = index_x * size_x
                y_pos = height - ((index_y + 1) * size_y)
                if column:
                    if self.shadow:
                        if app.piece_shadow:
                            shadow_color = self.color
                        else:
                            shadow_color = (0, 0, 0, 0)
                        element = draw_block(self.canvas, (x_pos, y_pos), (size_x, size_y), shadow_color, block='shadow')
                    else:
                        element = draw_block(self.canvas, (x_pos, y_pos), (size_x, size_y), self.color, block=self.name)
                else:
                    pass


class BGColumn(Widget):
    """Displays the background column color and/or image"""
    pass


class BG(Widget):
    """Displays the solid background color"""
    owner = ObjectProperty()


class Block(Widget):
    """old animated block widget, not used anymore, but could be useful at some point"""
    scale = NumericProperty(1)
    rotation = NumericProperty(0)
    block_type = StringProperty('')
    color = ListProperty([0, 0, 0, 0])
    animation = None
    modes = ['normal', 'fall', 'fall2', 'squish', 'explode', 'expand']

    def reset(self):
        self.stop_animate()
        self.opacity = 1
        self.rotation = 0
        self.scale = 1
        self.x = 0
        self.y = 0
        self.size_hint_y = 1

    def stop_animate(self):
        stop = False
        if self.animation is not None:
            self.animation.stop(self)
            stop = True
            self.animation = None
        return stop

    def animate_out(self, delay, duration, mode=None):
        app = App.get_running_app()
        self.stop_animate()
        self.animation = Animation(duration=delay)
        if mode == 'explode':
            xvect = (random.random() - 0.5) * app.button_scale * 5
            yvect = (random.random() - 0.5) * app.button_scale * 5
            rotation = (random.random() - 0.5) * 90
            self.animation += Animation(x=xvect, y=yvect, scale=0, rotation=rotation, duration=duration * 3)
        elif mode == 'expand':
            rotation = (random.random() - 0.5) * 180
            self.animation += Animation(opacity=0, rotation=rotation, scale=2, duration=duration * 2)
        elif mode == 'fall':
            self.animation += Animation(opacity=0, y=self.y-app.button_scale, duration=duration * 2)
        elif mode == 'fall2':
            self.animation += Animation(opacity=0, y=self.y-app.button_scale, rotation=60, duration=duration * 2)
        elif mode == 'squish':
            self.animation += Animation(opacity=0, size_hint_y=0, duration=duration * 2)
        else:
            self.animation += Animation(opacity=0, duration=duration * 2)
        self.animation.start(self)


class PlayLayout(RelativeLayout):
    """Custom layout widget that positions the play field, score, piece display areas, and various touch controls"""

    wider = BooleanProperty(False)
    field_height = NumericProperty(18)
    field_width = NumericProperty(10)
    piece_preview_padding = NumericProperty()
    owner = ObjectProperty()

    def on_size(self, *_):
        self.refresh_positions()

    def refresh_positions(self):
        app = App.get_running_app()
        touch_scale = app.touch_scale
        button_scale = .5 + (touch_scale / 2)
        field_height = self.field_height
        field_width = self.field_width
        owner = self.owner

        field_aspect = field_height / field_width
        spacing = 5
        self.wider = True if self.width > self.height else False
        play_area = owner.ids['playAreaBox']
        next_area = owner.ids['nextArea']
        stored_area = owner.ids['storedArea']
        score_area = owner.ids['scoreArea']

        extra_area = owner.ids['extraArea']
        name_area = owner.ids['nameArea']
        reaction_area = owner.ids['reactionArea']

        button_hd = owner.ids['hardDownButton']
        button_rleft = owner.ids['rotateLeftButton']
        button_left = owner.ids['moveLeftButton']
        button_down = owner.ids['moveDownButton']
        button_right = owner.ids['moveRightButton']
        button_rright = owner.ids['rotateRightButton']

        def reset_button(button):
            button.size = (0, 0)
            button.pos = (0, 0)

        def set_button(button, x, y, box, box_y=None):
            if box_y is None:
                box_y = box
            button.size = (box, box_y)
            button.pos = (x, y)

        top_height = app.button_scale / 2

        if self.wider:
            #horizontal layout
            if app.touch_area and (app.touch_rotate and app.touch_slide):
                box_divisor = 4
            else:
                box_divisor = 3
            box_max = self.height / 3

            play_area_width_max = int(self.height / field_aspect)
            play_area_width_min = int((self.height - top_height) / field_aspect)
            side_width_max = int((self.width - play_area_width_max) / 2)
            side_width_min = int((self.width - play_area_width_min) / 2)

            if side_width_max > box_max * 2:
                #widest
                play_area_width = play_area_width_max
                play_area_height = self.height
                side_width = side_width_max
                top_height = 0
                box = box_max
                move_downs = True
                score_area.size = (box - spacing, box)
                score_area.pos = (int(side_width - box) - spacing, self.height - box)
                score_area.orientation = 'vertical'
                smilies_width = side_width
                smilies_height = play_area_height - box - spacing

                if not app.touch_area:
                    name_area.pos = (self.width - (box * 2), 0)
                    name_area.size = (box * 2, box / 2)
                    name_area.opacity = 1
                    extra_area.size = (side_width, box * 1.5)
                    extra_area.pos = (self.width - side_width, box / 2)
                    extra_area.opacity = 1
                else:
                    extra_area.size = (box - spacing, box)
                    extra_area.pos = (side_width + play_area_width + spacing, self.height - box)
                    extra_area.opacity = 1
                    reset_button(name_area)
                    name_area.opacity = 0
            else:
                play_area_width = play_area_width_min
                play_area_height = self.height - top_height
                side_width = side_width_min
                score_area.size = (self.width, top_height)
                score_area.pos = (0, self.height - top_height)
                score_area.orientation = 'horizontal'
                move_downs = False
                box = min((self.height - top_height) / box_divisor, side_width) - spacing
                smilies_width = side_width
                smilies_height = play_area_height - box - spacing

                if not app.touch_area:
                    name_area.pos = (self.width - side_width, 0)
                    name_area.size = (side_width, box / 2)
                    name_area.opacity = 1
                    extra_area.size = (side_width, box * 1.5)
                    extra_area.pos = (self.width - side_width, box / 2)
                    extra_area.opacity = 1
                else:
                    reset_button(extra_area)
                    extra_area.opacity = 0
                    reset_button(name_area)
                    name_area.opacity = 0

            play_area.size = (play_area_width, play_area_height)
            play_area.pos = (side_width, 0)
            stored_pos_x = self.width - box
            set_button(stored_area, stored_pos_x, self.height - box - top_height, box)
            next_pos_x = 0
            set_button(next_area, next_pos_x, self.height - box - top_height, box)
            button_box = box * button_scale
            left_button_x = 0
            right_button_x = self.width - button_box

            def set_buttons(enabled, left_button, right_button, box, spacer, left_pos, right_pos, y_pos):
                if enabled and app.touch_area:
                    set_button(left_button, left_pos, y_pos, box)
                    set_button(right_button, right_pos, y_pos, box)
                    y_pos = y_pos + box + spacer
                else:
                    reset_button(left_button)
                    reset_button(right_button)
                return y_pos

            button_y = 0
            button_y = set_buttons(app.touch_slide, button_left, button_right, button_box, spacing, left_button_x, right_button_x, button_y)
            button_y = set_buttons(app.touch_rotate, button_rleft, button_rright, button_box, spacing, left_button_x, right_button_x, button_y)
            if move_downs:
                left_button_x += button_box
                right_button_x -= button_box
                smilies_x = left_button_x
                smilies_width = smilies_width - button_box
                button_y = 0
            else:
                smilies_x = 0
            button_y = set_buttons(True, button_down, button_hd, button_box, spacing, left_button_x, right_button_x, button_y)
            smilies_y = button_y
            smilies_height = smilies_height - smilies_y
            if app.connected:
                reaction_area.pos = (smilies_x, smilies_y)
                reaction_area.size = (smilies_width, smilies_height)
                reaction_area.opacity = 1
            else:
                reaction_area.opacity = 0
                reaction_area.pos = 0, 0
                reaction_area.size = 1, 1
        else:
            #vertical layout
            box = int(self.width / 5) - spacing
            box = box * button_scale

            reset_button(extra_area)
            extra_area.opacity = 0
            reset_button(name_area)
            name_area.opacity = 0

            score_area.size = (self.width, top_height)
            score_area.pos = (0, self.height - top_height)
            score_area.orientation = 'horizontal'

            bottom_height = box if app.touch_area else 0
            field_max_height = self.height - bottom_height - top_height
            right_side = int(self.width / 4)
            field_max_width = self.width - right_side - spacing
            set_button(next_area, self.width - right_side, self.height - right_side - top_height, right_side)
            set_button(stored_area, self.width - right_side, self.height - (right_side * 2) - spacing - top_height, right_side)
            smilies_height = self.height - top_height - (right_side * 2) - (spacing * 2)
            smilies_y = 0

            test_height = field_max_width * field_aspect
            if test_height > field_max_height:
                play_area_width = int(field_max_height / field_aspect)
                play_area_height = field_max_height
            else:
                play_area_width = field_max_width
                play_area_height = test_height
            play_area.size = (play_area_width, play_area_height)
            play_area_x = int((field_max_width - play_area_width) / 2)
            play_area.pos = (play_area_x, self.height - play_area_height - top_height)

            if app.touch_area:
                smilies_y = box + box + spacing + spacing
                smilies_height = smilies_height - smilies_y
                total_buttons = 1
                if app.touch_rotate:
                    total_buttons += 2
                if app.touch_slide:
                    total_buttons += 2
                if button_scale < 1:
                    button_width = box
                else:
                    button_width = int(self.width / total_buttons)

                set_button(button_hd, self.width - box, box + spacing, box)
                set_button(button_down, int((self.width - button_width) / 2), 0, button_width, box)
                if app.touch_rotate:
                    set_button(button_rleft, 0, 0, button_width, box)
                    set_button(button_rright, self.width - button_width, 0, button_width, box)
                    rotate_size = button_width
                else:
                    reset_button(button_rleft)
                    reset_button(button_rright)
                    rotate_size = 0
                if app.touch_slide:
                    set_button(button_left, rotate_size, 0, button_width, box)
                    set_button(button_right, self.width - button_width - rotate_size, 0, button_width, box)
                else:
                    reset_button(button_left)
                    reset_button(button_right)
            else:
                reset_button(button_hd)
                reset_button(button_down)
                reset_button(button_left)
                reset_button(button_right)
                reset_button(button_rleft)
                reset_button(button_rright)

            if app.connected:
                reaction_area.opacity = 1
                smilies_x = play_area_x + play_area_width
                reaction_area.pos = (smilies_x, smilies_y)
                reaction_area.size = (self.width - smilies_x, smilies_height)
            else:
                reaction_area.opacity = 0
                reaction_area.pos = 0, 0
                reaction_area.size = 1, 1


class GameOver(BoxLayout):
    """Widget that displays the game over animation"""

    def start(self, rows):
        animation_length = 1
        row_animation_length = animation_length / rows
        for index in range(rows):
            row = Image(source='data/bgrotated.png')
            row.allow_stretch = True
            row.keep_ratio = False
            row.opacity = 0
            animation = Animation(duration=row_animation_length*index) + Animation(opacity=1, duration=row_animation_length)
            animation.start(row)
            self.add_widget(row)


class GameOverInfo(BoxLayout):
    """Widget that displays stats about the recently ended game"""

    score = StringProperty()
    length = StringProperty()
    lines = StringProperty()
    pieces = StringProperty()
    win = BooleanProperty(True)
