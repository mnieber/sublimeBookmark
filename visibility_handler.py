from collections import defaultdict


def should_show_bookmark(window, bookmark):
    return window.project_file_name() == bookmark.project_path


def _sort_by_line_number(bookmarks):
    return sorted(bookmarks, key=lambda bookmark: bookmark.line_number)


def sort_bookmarks(visible_bookmarks, current_file):
    sorted_bookmarks = _sort_by_line_number(
        [b for b in visible_bookmarks if b.file_path == current_file])

    file_to_bookmarks = defaultdict(list)
    for bookmark in visible_bookmarks:
        if bookmark.file_path != current_file:
            file_to_bookmarks[bookmark.file_path].append(bookmark)

    for bookmarkList in file_to_bookmarks.values():
        sorted_bookmarks += _sort_by_line_number(bookmarkList)

    return sorted_bookmarks


def get_visible_bookmarks(bookmarks, window):
    return [b for b in bookmarks if should_show_bookmark(window, b)]
