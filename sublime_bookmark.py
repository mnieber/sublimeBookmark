import sublime
import sublime_plugin
import os.path
import uuid
from pickle import dump, load, UnpicklingError, PicklingError

from .common import (get_current_line_region, VERSION, log)
from .bookmark import Bookmark
from .visibility_handler import get_visible_bookmarks, sort_bookmarks, should_show_bookmark
from .ui import create_bookmark_panel_items, show_add_bookmark_dialog


# unmarks the given bookmark on the buffer
def _unmark_buffer(view, bookmark):
    view.erase_regions(bookmark.uid)


# marks the given bookmark on the buffer
def _mark_buffer(view, bookmark):
    view.add_regions(bookmark.uid, [bookmark.region], "text.plain", "bookmark",
                     sublime.DRAW_NO_FILL | sublime.DRAW_EMPTY_AS_OVERWRITE)


class SublimeBookmarkCommand(sublime_plugin.WindowCommand):
    def __init__(self, window):
        self.window = window
        self.active_view = self.window.active_view()
        self.bookmarks = []
        self.last_visited_bookmark = None

        # The bookmark to go to if the user cancels
        self.revert_bookmark = None

        self.database_path = os.path.join(
            os.path.dirname(sublime.packages_path()),
            'sublimeBookmarks.pickle')
        self._load()

    def run(self, type, name=None):
        self.active_view = self.window.active_view()

        # update bookmark positions. We need to do it anyway...
        self._update_bookmark_position()

        if type == "add":
            self._add_bookmark(name)

        elif type == "goto":
            self._create_bookmark_panel(self._hilight_done_callback)

        elif type == "remove":
            self._create_bookmark_panel(self._remove_done_callback)

        elif type == "remove_all":
            self._remove_all_bookmarks_and_save()

        elif type == "goto_next":
            self._step(1)

        elif type == "goto_previous":
            self._step(-1)

        # ASYNC OPERATIONS
        elif type == "mark_buffer":
            for bookmark in self.bookmarks:
                self._update_buffer_status(bookmark)

        elif type == "move_bookmarks":
            self._update_bookmark_position()

    def _create_bookmark_panel(self, on_done):
        # if no bookmarks are acceptable, don't show bookmarks
        self.bookmarks_in_panel = sort_bookmarks(
            get_visible_bookmarks(self.bookmarks, self.window),
            self.active_view.file_name())

        if len(self.bookmarks_in_panel) == 0:
            return

        self.revert_bookmark = self._create_revert_bookmark()

        # create a selection panel and launch it
        sublime.capturing_quick_panel_view = True
        start_index = 0
        self.window.show_quick_panel(
            create_bookmark_panel_items(self.window, self.bookmarks_in_panel),
            on_done, sublime.KEEP_OPEN_ON_FOCUS_LOST, start_index,
            self._goto_bookmark_in_panel_with_index)

    def _remove_bookmark(self, bookmark):
        for view in self.window.views():
            if bookmark.is_my_view(view):
                _unmark_buffer(view, bookmark)
        self.bookmarks.remove(bookmark)

    # Event handlers
    def _add_bookmark(self, name):
        if name:
            log("no name")
            self._add_bookmark_callback(name)
        else:
            view = self.window.active_view()
            region = get_current_line_region(view)

            # copy whatever is on the line for the bookmark name
            initial_text = view.substr(region).strip()
            show_add_bookmark_dialog(self.window, "Add Bookmark", initial_text,
                                     self._add_bookmark_callback, None)

    def _remove_all_bookmarks_and_save(self):
        for bookmark in self.bookmarks:
            self._remove_bookmark(bookmark)
        self._save()

    def _step(self, step_size):
        visible_bookmarks = get_visible_bookmarks(self.bookmarks, self.window)
        try:
            current_index = visible_bookmarks.index(self.last_visited_bookmark)
            next_index = (current_index + step_size) % len(visible_bookmarks)
        except ValueError:
            next_index = 0
        if next_index >= 0 and next_index < len(visible_bookmarks):
            self._goto_bookmark(visible_bookmarks[next_index])

    def _update_buffer_status(self, bookmark):
        if self.active_view is None:
            return

        should_show = should_show_bookmark(self.window, bookmark)
        valid_context = bookmark.is_my_view(self.active_view)

        if valid_context and should_show:
            _mark_buffer(self.active_view, bookmark)
        else:
            _unmark_buffer(self.active_view, bookmark)

    def _update_bookmark_position(self):
        for bookmark in self.bookmarks:
            if bookmark.is_my_view(
                    self.active_view) and not self.active_view.is_loading():
                bookmark.update_data(self.active_view)
                self._update_buffer_status(bookmark)
        self._save()

    # helpers
    # creates a bookmark that keeps track of where we were before opening
    # n options menu.
    def _create_revert_bookmark(self):
        uid = "revert_bookmark"
        name = ""
        return Bookmark(uid, name, self.window.project_file_name(),
                        self.active_view)

    def _restore_quick_panel_focus(self):
        """Restore focus to quick panel is as easy as focus in the quick panel view, that the eventListener has previously captured and saved"""
        if getattr(sublime, 'quick_panel_view', None):
            self.window.focus_view(sublime.quick_panel_view)

    def _goto_bookmark(self, bookmark):
        view = self.window.find_open_file(bookmark.file_path)
        if view:
            self.window.focus_view(view)
            self.last_visited_bookmark = bookmark
            sublime.set_timeout(self._restore_quick_panel_focus, 100)
            # self.window.focus_view(view)
            view.show_at_center(bookmark.region)

            # move cursor to the middle of the bookmark's region
            bookmark_region_mid = 0.5 * (
                bookmark.region.begin() + bookmark.region.end())
            move_region = sublime.Region(bookmark_region_mid,
                                         bookmark_region_mid)
            view.sel().clear()
            view.sel().add(move_region)

    # goes to the revert bookmark
    def _goto_revert_bookmark(self):
        if self.revert_bookmark:
            self._goto_bookmark(self.revert_bookmark)
            self.revert_bookmark = None

    # callbacks---------------------------------------------------
    def _add_bookmark_callback(self, name):
        # get region and line data
        region = get_current_line_region(self.active_view)

        line_str = self.active_view.substr(region)
        if not line_str.strip():
            sublime.status_message(
                "SublimeBookmarks: Bookmark Empty. Not Creating Bookmark")
            return

        bookmark = Bookmark(uuid.uuid4().hex, name,
                            self.window.project_file_name(), self.active_view)
        self.bookmarks.append(bookmark)
        self._update_buffer_status(bookmark)
        self._save()

    # display highlighted bookmark
    def _goto_bookmark_in_panel_with_index(self, index):
        self._goto_bookmark(self.bookmarks_in_panel[index])

    # if the user canceled, go back to the original file
    def _hilight_done_callback(self, index):
        if index == -1:
            self._goto_revert_bookmark()
        else:
            bookmark = self.bookmarks_in_panel[index]
            self.window.open_file(bookmark.file_path)

            def _go():
                self._update_buffer_status(bookmark)
                self._goto_bookmark(bookmark)

            sublime.set_timeout(_go, 200)

    # remove the selected bookmark or go back if user cancelled
    def _remove_done_callback(self, index):
        if index == -1:
            self._goto_revert_bookmark()
        else:
            bookmark = self.bookmarks_in_panel[index]
            self.window.open_file(bookmark.file_path)

            def _go():
                self._goto_bookmark(bookmark)
                self._remove_bookmark(bookmark)

            sublime.set_timeout(_go, 200)

        self._save()

    # Save Load
    def _load(self):
        log("Loading bookmarks from %s" % self.database_path)
        try:
            with open(self.database_path, "rb") as ifs:
                if load(ifs) != VERSION:
                    raise UnpicklingError("version difference in files")
                self.bookmarks = load(ifs)
        except (OSError, IOError, UnpicklingError, EOFError,
                BaseException) as e:
            print("\nException:------- ")
            print(e)
            print("\nUnable To Load Bookmarks. Nuking Load File")
            # clear the load file :]
            open(self.database_path, "wb").close()
            # if you can't load, try and save a "default" state
            self._save()

    def _save(self):
        try:
            with open(self.database_path, "wb") as ofs:
                dump(VERSION, ofs)
                dump(self.bookmarks, ofs)
        except (OSError, IOError, PicklingError) as e:
            print(e)
            print("\nUnable To Save Bookmarks. Please Contact Dev")
