import re
import fnmatch
import os
import datetime
import string
from kivy.app import App
from kivy.clock import Clock
from kivy.properties import ObjectProperty, StringProperty, ListProperty, BooleanProperty, NumericProperty, DictProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.utils import platform
from kivy.animation import Animation
from kivy.uix.widget import Widget
if platform == 'win':
    from ctypes import windll, create_unicode_buffer

from generalelements import NormalPopup

from kivy.lang.builder import Builder
Builder.load_string("""
<SelectableRecycleBoxLayout>:
    default_size_hint: 1, None
    default_size: self.width, app.button_scale
    spacing: 2
    size_hint_x: 1
    orientation: 'vertical'
    size_hint_y: None
    height: self.minimum_height
    multiselect: False
    touch_multiselect: False

<RecycleItem>:
    canvas.before:
        Color:
            rgba: self.bgcolor
        Rectangle:
            pos: self.pos
            size: self.size
    canvas.after:
        Color:
            rgba: app.overlay_color if app.selected_object == self else (1, 1, 1, 0)
        Rectangle:
            size: self.size
            pos: self.pos
    size_hint_x: 1
    height: app.button_scale

<InputPopup>:
    cols:1
    NormalLabel:
        text: root.text
    NormalInput:
        id: input
        multiline: False
        hint_text: root.hint
        input_filter: app.test_album
        text: root.input_text
        focus: True
    Label:
    GridLayout:
        cols: 2
        size_hint_y: None
        height: app.button_scale
        WideButton:
            text: root.yes_text
            warn: root.warn_yes
            on_release: root.dispatch('on_answer','yes')
        WideButton:
            text: root.no_text
            warn: root.warn_no
            on_release: root.dispatch('on_answer', 'no')

<ConfirmPopup>:
    cols:1
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
            warn: root.warn_yes
        WideButton:
            text: root.no_text
            on_release: root.dispatch('on_answer', 'no')
            warn: root.warn_no

<ClickFade>:
    canvas:
        Color:
            rgba: 1, 1, 1, .5
        Rectangle:
            size: self.size
            pos: root.pos
    size_hint: None, None
    opacity: 0

<FileBrowser>:
    wider: True if self.width > self.height else False
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: app.button_scale
            NormalButton:
                text: 'Go Up'
                on_release: root.go_up()
            ShortLabel:
                text: root.path
                size_hint_y: None
                height: app.button_scale
        BoxLayout:
            size_hint: 1, 1
            pos: root.pos
            spacing: app.button_scale / 4
            orientation: 'horizontal'
            BoxLayout:
                orientation: 'vertical'
                size_hint: 1, 1
                NormalRecycleView:
                    size_hint_x: 1
                    id: fileList
                    viewclass: 'FileBrowserItem'
                    FileBrowserSelectableRecycleBoxLayout:
                        id: files
                        multiselect: root.multiselect
                        owner: root
                BoxLayout:
                    disabled: not root.edit_folders
                    opacity: 0 if self.disabled else 1
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: 0 if self.disabled else app.button_scale
                    NormalButton:
                        height: app.button_scale
                        text: 'Create Folder...'
                        on_release: root.add_folder()
                    NormalButton:
                        height: app.button_scale
                        text: 'Delete This Folder'
                        disabled: not root.can_delete_folder
                        warn: True
                        on_release: root.delete_folder()
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: 1
                size_hint_x: .5 if root.wider else .75
                NormalRecycleView:
                    size_hint_x: 1
                    id: locationsList
                    viewclass: 'FileBrowserItem'
                    FileBrowserSelectableRecycleBoxLayout:
                        multiselect: False
                        owner: root
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: app.button_scale
            NormalInput:
                id: filename
                size_hint_y: None
                opacity: 1 if not root.directory_select else 0
                disabled: not root.file_editable
                size_hint_x: 1
                text: root.file
                on_text: root.file = self.text
            NormalButton:
                text: root.ok_text
                disabled: not (root.target_selected or (root.export_mode and len(root.file) > 0) or root.allow_no_file)
                on_release: root.dispatch('on_ok')
            NormalButton:
                text: root.cancel_text
                on_release: root.dispatch('on_cancel')

<FileBrowserItem>:
    Image:
        size_hint_x: None
        width: app.button_scale
        source: 'atlas://data/images/defaulttheme/filechooser_%s' % ('folder' if root.type == 'folder' else 'file')
    NormalLabel:
        size_hint_y: None
        height: app.button_scale
        text_size: (self.width - 20, None)
        text: root.text
        halign: 'left'
        valign: 'center'
    NormalLabel:
        size_hint_x: 0 if root.is_folder else 0.25
        text: root.file_size
    NormalLabel:
        size_hint_x: 0 if root.is_folder else 0.333
        text: root.modified

""")


def format_size(size):
    """Formats a file size in bytes to human-readable format.
    Accepts a numerical value, returns a string.
    """

    if size >= 1024:
        size = size/1024
        if size >= 1024:
            size = size/1024
            if size >= 1024:
                size = size/1024
                return str(round(size, 2))+' GB'
            else:
                return str(round(size, 2))+' MB'
        else:
            return str(round(size, 2))+' KB'
    else:
        return str(round(size, 2))+' Bytes'


def tryint(s):
    try:
        return int(s)
    except ValueError:
        return s


def alphanum_key(s):
    return [tryint(c) for c in re.split('([0-9]+)', s)]


def sort_nicely(l):
    return sorted(l, key=alphanum_key)


def get_drives():
    drives = []
    if platform == 'win':
        for path in ['Desktop', 'Documents', 'Pictures']:
            drives.append((os.path.expanduser(u'~') + os.path.sep + path + os.path.sep, path))
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                name = create_unicode_buffer(64)
                # get name of the drive
                drive = letter + u':'
                windll.kernel32.GetVolumeInformationW(drive + os.path.sep, name, 64, None, None, None, None, 0)
                drive_name = drive
                if name.value:
                    drive_name = drive_name + '(' + name.value + ')'
                drives.append((drive + os.path.sep, drive_name))
            bitmask >>= 1
    elif platform == 'linux':
        drives.append((os.path.sep, os.path.sep))
        drives.append((os.path.expanduser(u'~') + os.path.sep, 'Home'))
        drives.append((os.path.sep + u'mnt' + os.path.sep, os.path.sep + u'mnt'))
        places = (os.path.sep + u'mnt' + os.path.sep, os.path.sep + u'media')
        for place in places:
            if os.path.isdir(place):
                for directory in next(os.walk(place))[1]:
                    drives.append((place + os.path.sep + directory + os.path.sep, directory))
    elif platform == 'macosx' or platform == 'ios':
        drives.append((os.path.expanduser(u'~') + os.path.sep, 'Home'))
        vol = os.path.sep + u'Volume'
        if os.path.isdir(vol):
            for drive in next(os.walk(vol))[1]:
                drives.append((vol + os.path.sep + drive + os.path.sep, drive))
    elif platform == 'android':
        paths = [
            ('/', 'Root'),
            ('/storage', 'Mounted Storage')
        ]
        from android.storage import primary_external_storage_path
        primary_ext_storage = primary_external_storage_path()
        if primary_ext_storage:
            paths.append((primary_ext_storage, 'Primary Storage'))

        from android.storage import secondary_external_storage_path
        secondary_ext_storage = secondary_external_storage_path()
        if secondary_ext_storage:
            paths.append((secondary_ext_storage, 'Secondary Storage'))

        for path in paths:
            realpath = os.path.realpath(path[0]) + os.path.sep
            if os.path.exists(realpath):
                drives.append((realpath, path[1]))

    return drives


class RecycleItem(RecycleDataViewBehavior, BoxLayout):
    selectable_item = BooleanProperty(True)
    bgcolor = ListProperty([0, 0, 0, 0])
    owner = ObjectProperty()
    text = StringProperty()
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)
    index = NumericProperty(0)
    data = {}

    def trigger_action(self, *_):
        self.parent.click_node(self)

    def on_selected(self, *_):
        self.set_color()

    def set_color(self):
        app = App.get_running_app()

        if self.selected:
            self.bgcolor = app.theme.selected
        else:
            if self.index % 2 == 0:
                self.bgcolor = (0, 0, 0, .1)
            else:
                self.bgcolor = (0, 0, 0, 0)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.data = data
        self.set_color()
        return super(RecycleItem, self).refresh_view_attrs(rv, index, data)

    def apply_selection(self, rv, index, is_selected):
        self.selected = is_selected

    def on_touch_down(self, touch):
        if super(RecycleItem, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos):
            app = App.get_running_app()
            self.parent.click_node(self)
            if app.shift_pressed:
                self.parent.select_range(self.index, touch)
            return True


class SelectableRecycleBoxLayout(RecycleBoxLayout, LayoutSelectionBehavior):
    """Adds selection and focus behavior to the view."""
    owner = ObjectProperty()
    selected = DictProperty()
    selects = ListProperty()
    multiselect = BooleanProperty(False)

    def clear_selects(self):
        self.selects = []

    def refresh_selection(self):
        for node in self.children:
            try:  #possible for nodes to not be synched with data
                data = self.parent.data[node.index]
                selected = data['selected']
                node.selected = selected
            except:
                pass

    def deselect_all(self):
        for data in self.parent.data:
            data['selected'] = False
        self.refresh_selection()
        self.selects = []
        self.selected = {}

    def select_all(self):
        self.selects = []
        selects = []
        for data in self.parent.data:
            if data['selectable']:
                data['selected'] = True
                selects.append(data)
        self.selects = selects
        if self.selects:
            self.selected = selects[-1]
        self.refresh_selection()

    def select_node(self, node):
        super().select_node(node)
        if not self.multiselect:
            self.deselect_all()
        node.selected = True
        self.selects.append(node.data)
        self.parent.data[self.parent.data.index(node.data)]['selected'] = True
        node.data['selected'] = True
        self.selected = node.data

    def deselect_node(self, node):
        super().deselect_node(node)
        if node.data in self.selects:
            self.selects.remove(node.data)
        if self.selected == node.data:
            if self.selects:
                self.selected = self.selects[-1]
            else:
                self.selected = {}
        if node.data in self.parent.data:
            parent_index = self.parent.data.index(node.data)
            parent_data = self.parent.data[parent_index]
            parent_data['selected'] = False
        node.selected = False
        node.data['selected'] = False

    def click_node(self, node):
        #Called by a child widget when it is clicked on
        if node.selected:
            if self.multiselect:
                self.deselect_node(node)
            else:
                pass
                #self.deselect_all()
        else:
            if not self.multiselect:
                self.deselect_all()
            self.select_node(node)
            self.selected = node.data

    def select_range(self, *_):
        if self.multiselect and self.selected and self.selected['selectable']:
            select_index = self.parent.data.index(self.selected)
            selected_nodes = []
            if self.selects:
                for select in self.selects:
                    if select['selectable']:
                        index = self.parent.data.index(select)
                        if index != select_index:
                            selected_nodes.append(index)
            else:
                selected_nodes = [0, len(self.parent.data)]
            closest_node = min(selected_nodes, key=lambda x: abs(x-select_index))

            for index in range(min(select_index, closest_node), max(select_index, closest_node)):
                selected = self.parent.data[index]
                selected['selected'] = True
                if selected not in self.selects:
                    self.selects.append(selected)

            self.parent.refresh_from_data()

    def toggle_select(self, *_):
        if self.multiselect:
            if self.selects:
                self.deselect_all()
            else:
                self.select_all()
        else:
            if self.selected:
                self.selected = {}


class InputPopup(GridLayout):
    """Basic text input popup message.  Calls 'on_answer' when either button is clicked."""

    yes_text = StringProperty('OK')
    warn_yes = BooleanProperty(False)
    no_text = StringProperty('Cancel')
    warn_no = BooleanProperty(False)
    input_text = StringProperty()
    text = StringProperty()  #Text that the user has input
    hint = StringProperty()  #Grayed-out hint text in the input field

    def __init__(self, **kwargs):
        self.register_event_type('on_answer')
        super(InputPopup, self).__init__(**kwargs)

    def on_answer(self, *args):
        pass


class ConfirmPopup(GridLayout):
    """Basic Yes/No popup message.  Calls 'on_answer' when either button is clicked."""

    text = StringProperty()
    yes_text = StringProperty('Yes')
    no_text = StringProperty('No')
    warn_yes = BooleanProperty(False)
    warn_no = BooleanProperty(False)

    def __init__(self, **kwargs):
        self.register_event_type('on_answer')
        super(ConfirmPopup, self).__init__(**kwargs)

    def on_answer(self, *args):
        pass


class ClickFade(Widget):
    animation = None

    def begin(self, mode='opacity'):
        app = App.get_running_app()
        self.opacity = 0

        if app.animations:
            if self.animation:
                self.animation.cancel(self)
            if mode == 'height':
                self.animation = Animation(opacity=1, duration=(app.animation_length / 4)) + Animation(height=0, pos=(self.pos[0], self.pos[1]+self.height), duration=(app.animation_length / 2))
            else:
                self.animation = Animation(opacity=1, duration=(app.animation_length / 4)) + Animation(opacity=0, duration=(app.animation_length / 2))
            self.animation.start(self)
            self.animation.bind(on_complete=self.finish_animation)
        else:
            self.finish_animation()

    def finish_animation(self, *_):
        self.animation = None
        try:
            self.parent.remove_widget(self)
        except:
            pass


class FileBrowserSelectableRecycleBoxLayout(SelectableRecycleBoxLayout):
    def click_node(self, node):
        super().click_node(node)
        self.owner.click_node(node)

    def on_selected(self, *_):
        self.owner.select_item(self.selected)

    def on_selects(self, *_):
        self.owner.select_items(self.selects)


class FileBrowser(FloatLayout):
    __events__ = ('on_cancel', 'on_ok')
    path = StringProperty()
    file = StringProperty()
    files = ListProperty()
    folder_files = ListProperty()
    filename = StringProperty()
    root = StringProperty()
    allow_no_file = BooleanProperty(False)
    clickfade_object = ObjectProperty(allownone=True)

    popup = ObjectProperty(None, allownone=True)
    remember = None
    can_delete_folder = BooleanProperty(False)

    edit_folders = BooleanProperty(True)
    multiselect = BooleanProperty(False)
    new_folder = StringProperty('')
    start_in = StringProperty()
    directory_select = BooleanProperty(False)
    file_editable = BooleanProperty(False)
    filters = ListProperty()
    target_selected = BooleanProperty(False)
    export_mode = BooleanProperty(False)
    autoselect = BooleanProperty(False)

    header_text = StringProperty('Select A File')
    cancel_text = StringProperty('Cancel')
    ok_text = StringProperty('OK')

    def __init__(self, **kwargs):
        if not self.start_in:
            self.start_in = '/'
        Clock.schedule_once(self.refresh_locations)
        self.clickfade_object = ClickFade()
        super(FileBrowser, self).__init__(**kwargs)

    def clickfade(self, widget):
        try:
            self.remove_widget(self.clickfade_object)
        except:
            pass
        self.clickfade_object.size = widget.size
        self.clickfade_object.pos = widget.to_window(*widget.pos)
        self.clickfade_object.begin()
        self.add_widget(self.clickfade_object)

    def toggle_select(self):
        file_list = self.ids['files']
        if self.multiselect:
            file_list.toggle_select()

    def get_selected(self):
        file_list = self.ids['files']
        selected = file_list.selects
        return selected

    def dismiss_popup(self, *_):
        """If this dialog has a popup, closes it and removes it."""

        if self.popup:
            self.popup.dismiss()
            self.popup = None

    def add_folder(self):
        """Starts the add folder process, creates an input text popup."""

        content = InputPopup(hint='Folder Name', text='Enter A Folder Name:')
        app = App.get_running_app()
        content.bind(on_answer=self.add_folder_answer)
        self.popup = NormalPopup(title='Create Folder', content=content, size_hint=(None, None), size=(app.popup_x, app.button_scale * 5), auto_dismiss=False)
        self.popup.open()

    def add_folder_answer(self, instance, answer):
        """Tells the app to rename the folder if the dialog is confirmed.
        Arguments:
            instance: The dialog that called this function.
            answer: String, if 'yes', the folder will be created, all other answers will just close the dialog.
        """

        if answer == 'yes':
            text = instance.ids['input'].text.strip(' ')
            if text:
                app = App.get_running_app()
                folder = os.path.join(self.path, text)
                created = False
                try:
                    if not os.path.isdir(folder):
                        os.makedirs(folder)
                        created = True
                except:
                    pass
                if created:
                    app.message("Created the folder '"+folder+"'")
                    self.path = folder
                    self.refresh_folder()
                else:
                    app.message("Could Not Create Folder.")
        self.dismiss_popup()

    def delete_folder(self):
        """Starts the delete folder process, creates the confirmation popup."""

        app = App.get_running_app()
        text = "Delete The Selected Folder?"
        content = ConfirmPopup(text=text, yes_text='Delete', no_text="Don't Delete", warn_yes=True)
        content.bind(on_answer=self.delete_folder_answer)
        self.popup = NormalPopup(title='Confirm Delete', content=content, size_hint=(None, None), size=(app.popup_x, app.button_scale * 4), auto_dismiss=False)
        self.popup.open()

    def delete_folder_answer(self, instance, answer):
        """Tells the app to delete the folder if the dialog is confirmed.
        Arguments:
            instance: The dialog that called this function.
            answer: String, if 'yes', the folder will be deleted, all other answers will just close the dialog.
        """

        del instance
        if answer == 'yes':
            app = App.get_running_app()
            try:
                os.rmdir(self.path)
                app.message("Deleted Folder: \""+self.path+"\"")
                self.go_up()
            except:
                app.message("Could Not Delete Folder...")
        self.dismiss_popup()

    def reset_folder_position(self, *_):
        filelist = self.ids['fileList']
        filelist.scroll_y = 1

    def refresh_locations(self, *_):
        locations_list = self.ids['locationsList']
        locations = get_drives()
        self.root = locations[0][0]
        data = []
        for location in locations:
            data.append({
                'text': location[1],
                'fullpath': location[0],
                'path': location[0],
                'type': 'folder',
                'is_folder': True,
                'owner': self,
                'selectable': False
            })
        locations_list.data = data
        if not self.path:
            self.path = locations[0][0]
        self.refresh_folder()

    def refresh_folder(self, *_):
        file_list = self.ids['fileList']
        files = self.ids['files']
        files.selects = []
        data = []
        files = []
        dirs = []

        walk = os.walk
        for root, list_dirs, list_files in walk(self.path, topdown=True):
            dirs = list_dirs[:]
            list_dirs.clear()
            files = list_files

        self.folder_files = files
        if dirs or files:
            self.can_delete_folder = False
        else:
            self.can_delete_folder = True
        dirs = sorted(dirs, key=lambda s: s.lower())
        for directory in dirs:
            fullpath = os.path.join(self.path, directory)
            data.append({
                'text': directory,
                'fullpath': fullpath,
                'path': fullpath + os.path.sep,
                'type': 'folder',
                'file': '',
                'owner': self,
                'is_folder': True,
                'selected': False,
                'multiselect': self.multiselect,
                'selectable': self.directory_select,
                'file_size': '',
                'modified': ''
            })
        if not self.directory_select:
            if self.filters:
                filtered_files = []
                for item in self.filters:
                    filtered_files += fnmatch.filter(files, item)
                files = filtered_files
            #files = sorted(files, key=lambda s: s.lower())
            files = sort_nicely(files)
            for file in files:
                fullpath = os.path.join(self.path, file)
                file_size = int(os.path.getsize(fullpath))
                modified = int(os.path.getmtime(fullpath))
                data.append({
                    'text': file,
                    'fullpath': fullpath,
                    'path': self.path,
                    'type': file,
                    'file': file,
                    'owner': self,
                    'is_folder': False,
                    'selected': False,
                    'multiselect': self.multiselect,
                    'selectable': True,
                    'file_size': format_size(file_size),
                    'modified': datetime.datetime.fromtimestamp(modified).strftime('%Y-%m-%d, %I:%M%p')
                })

        file_list.data = data
        if not self.directory_select:
            if self.export_mode:
                if not self.file:
                    self.target_selected = False
                else:
                    self.target_selected = True
            else:
                self.file = ''
                self.filename = ''
                self.target_selected = False
        else:
            self.file = ''
            self.filename = ''
            self.target_selected = True

        self.reset_folder_position()
        if self.autoselect:
            self.toggle_select()

    def go_up(self, *_):
        up_path = os.path.realpath(os.path.join(self.path, '..'))
        if not up_path.endswith(os.path.sep):
            up_path += os.path.sep
        if up_path == self.path:
            up_path = self.root
        self.path = up_path
        self.refresh_folder()

    def double_click(self, instance):
        if self.target_selected and not self.export_mode:
            self.dispatch('on_ok')

    def click_node(self, node):
        self.clickfade(node)
        item = node.data
        if item['type'] == 'folder':
            self.path = item['path']
            self.refresh_folder()

    def select_item(self, item):
        if item:
            if not self.directory_select and item['type'] != 'folder':
                self.filename = item['fullpath']
                self.file = item['file']
                self.target_selected = True
        else:
            if not self.directory_select:
                self.target_selected = False
            if not self.export_mode:
                self.filename = ''
                self.file = ''

    def select_items(self, items):
        self.files = []
        for item in items:
            if 'file' in item:
                self.files.append(item['file'])

    def on_cancel(self):
        pass

    def on_ok(self):
        pass


class FileBrowserItem(RecycleItem):
    path = StringProperty()
    fullpath = StringProperty()
    file = StringProperty()
    type = StringProperty('folder')
    multiselect = BooleanProperty(False)
    file_size = StringProperty()
    modified = StringProperty()
    is_folder = BooleanProperty(True)

    def on_selected(self, *_):
        if self.type == 'folder' and self.multiselect and self.selected:
            self.selected = False

        self.set_color()

    def on_touch_down(self, touch):
        if not self.multiselect and touch.is_double_tap and self.collide_point(*touch.pos):
            if self.parent.owner:
                filebrowser = self.parent.owner
                filebrowser.double_click(self)
        else:
            super(FileBrowserItem, self).on_touch_down(touch)
