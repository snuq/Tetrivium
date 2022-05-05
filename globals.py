from collections import OrderedDict
from kivy.utils import platform
if platform in ['win', 'linux', 'macosx', 'unknown']:
    desktop = True
else:
    desktop = False

app_name = 'Tetrivium'
fps = 30
color_names = 'button_down', 'button_up', 'button_text', 'button_toggle_true', 'button_toggle_false', 'button_disabled', 'button_disabled_text', 'slider_background', 'slider_grabber', 'input_background', 'header_background', 'header_text', 'text', 'disabled_text', 'selected', 'indented', 'background', 'background_overlay', 'background_column', 'shadow_color', 'I', 'J', 'L', 'O', 'S', 'Z', 'T'
#             0   1       2       3       4       5       6       7       8       9       10     11      12      13      14      15      16      17      18      19      20      21      22
levels_60 = [53,  49,     45,     41,     37,     33,     28,     22,     17,     11,     10,     9,      8,      7,      6,      6,      5,      5,      4,      4,      3,      3,      2]
levels = [.88333, .81667, .75000, .68333, .61667, .55000, .46667, .36667, .28333, .18333, .16667, .15000, .13333, .11667, .10000, .10000, .08333, .08333, .06667, .06667, .05000, .05000, .03333]
clear_modes = ['normal', 'reverse', 'random', 'inward', 'outward']
app = None
default_bg = [0, 0, 0, 1]
multiplayer_port = 25065

navigation_next = [274, 12, -12]
navigation_prev = [273, 11, -11]
navigation_activate = [13, 0, 21]
navigation_back = [1, -1, 22]
navigation_left = [276, 13, -13]
navigation_right = [275, 14, -14]

default_c_left = [276, 260, -13]
default_c_right = [275, 262, -14]
default_c_rotate_l = [305, 306, 263, -1]
default_c_rotate_r = [273, 307, 308, 265, 0]
default_c_down = [274, 261, 1073741980, -12]
default_c_drop = [32, 258, -2]
default_c_store = [13, 271, -3]
default_c_pause = [8, -6]

pieces = OrderedDict([
    ('I', {
        'name': 'I',
        'shapes': [
            [
                [False, False, False, False],
                [False, False, False, False],
                [True, True, True, True],
                [False, False, False, False],
            ],
            [
                [False, True, False, False],
                [False, True, False, False],
                [False, True, False, False],
                [False, True, False, False],
            ]
        ],
        'offset': 3}),
    ('J', {
        'name': 'J',
        'shapes': [
            [
                [False, False, False],
                [True, True, True],
                [False, False, True]
            ],
            [
                [False, True, False],
                [False, True, False],
                [True, True, False]
            ],
            [
                [True, False, False],
                [True, True, True],
                [False, False, False]
            ],
            [
                [False, True, True],
                [False, True, False],
                [False, True, False]
            ]
        ],
        'offset': 3}),
    ('L', {
        'name': 'L',
        'shapes': [
            [
                [False, False, False],
                [True, True, True],
                [True, False, False]
            ],
            [
                [True, True, False],
                [False, True, False],
                [False, True, False]
            ],
            [
                [False, False, True],
                [True, True, True],
                [False, False, False]
            ],
            [
                [False, True, False],
                [False, True, False],
                [False, True, True]
            ]
        ],
        'offset': 3}),
    ('O', {
        'name': 'O',
        'shapes': [
            [
                [False, False, False, False],
                [False, True, True, False],
                [False, True, True, False],
                [False, False, False, False]
            ]
        ],
        'offset': 2}),
    ('S', {
        'name': 'S',
        'shapes': [
            [
                [False, False, False],
                [False, True, True],
                [True, True, False]
            ],
            [
                [True, False, False],
                [True, True, False],
                [False, True, False]
            ]
        ],
        'offset': 3}),
    ('Z', {
        'name': 'Z',
        'shapes': [
            [
                [False, False, False],
                [True, True, False],
                [False, True, True]
            ],
            [
                [False, True, False],
                [True, True, False],
                [True, False, False]
            ]
        ],
        'offset': 3}),
    ('T', {
        'name': 'T',
        'shapes': [
            [
                [False, False, False],
                [True, True, True],
                [False, True, False]
            ],
            [
                [False, True, False],
                [True, True, False],
                [False, True, False]
            ],
            [
                [False, True, False],
                [True, True, True],
                [False, False, False]
            ],
            [
                [False, True, False],
                [False, True, True],
                [False, True, False]
            ]
        ],
        'offset': 3})
])

emotions_colors = {
    'evil': (0.7, 0, 0),
    'happy': (0.8, 0.8, 0),
    'laugh': (0, 0.7, 0),
    'mad': (1, 0, 0),
    'neutral': (0.4, 0.4, 0.4),
    'sad': (0, 0, 0.7),
    'surprised': (0.7, 0, 0.7),
    'unamused': (0.25, 0.5, 0.5),
    'wink': (0.7, 0.5, 0)
}
