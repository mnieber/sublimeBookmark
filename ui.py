def show_add_bookmark_dialog(window, caption, initial_text, on_done,
                             on_cancel):
    input_panel_view = window.show_input_panel(caption, initial_text, on_done,
                                               None, on_cancel)

    # select the text in the view so that
    # when the user types a new name, the old name is overwritten
    assert (len(input_panel_view.sel()) > 0)
    selection_region = input_panel_view.full_line(input_panel_view.sel()[0])
    input_panel_view.sel().add(selection_region)


def create_bookmark_panel_items(window, visible_bookmarks):
    def ellipsis_string_end(string, length):
        # I have NO idea why the hell this would happen. But it's happening.
        if string is None:
            return ""
        else:
            if len(string) <= length:
                return string
            else:
                return string[0:length - 3] + '.' * 3

    def ellipsis_string_begin(string, length):
        if string is None:
            return ""
        else:
            if len(string) <= length:
                return string
            else:
                return '.' * 3 + string[len(string) + 3 - (length):len(string)]

    bookmark_items = []

    for bookmark in visible_bookmarks:
        bookmark_name = ellipsis_string_end(bookmark.name, 55)

        bookmark_line = bookmark.line_str.lstrip()
        file_path = bookmark.file_path.lstrip()
        bookmark_file = ellipsis_string_begin(file_path, 55)

        bookmark_items.append([bookmark_name, bookmark_line, bookmark_file])

    return bookmark_items
