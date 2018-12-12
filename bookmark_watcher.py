import sublime
import sublime_plugin


class BookmarkWatcher(sublime_plugin.EventListener):
    def on_activated(self, view):
        """This method is called whenever a view (tab, quick panel, etc.) gains focus, but we only want to get the quick panel view, so we use a flag"""
        if getattr(sublime, 'capturing_quick_panel_view', False):
            sublime.capturing_quick_panel_view = False
            """View saved as an attribute of the global variable sublime so it can be accesed from your plugin or anywhere"""
            sublime.quick_panel_view = view

    def on_activated_async(self, view):
        sublime.active_window().run_command("sublime_bookmark",
                                            {"type": "mark_buffer"})
        sublime.active_window().run_command("sublime_bookmark",
                                            {"type": "move_bookmarks"})

    def on_modified_async(self, view):
        sublime.active_window().run_command("sublime_bookmark",
                                            {"type": "move_bookmarks"})

    def on_deactivated_async(self, view):
        sublime.active_window().run_command("sublime_bookmark",
                                            {"type": "mark_buffer"})
        sublime.active_window().run_command("sublime_bookmark",
                                            {"type": "move_bookmarks"})

    # Must be on close
    # not on pre close. on pre-close,the view still exists
    def on_close(self, view):
        pass

    def on_pre_save_async(self, view):
        pass
        # sublime.run_command("sublime_bookmark", {"type": "save_data" } )
