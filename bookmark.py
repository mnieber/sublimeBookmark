from .common import get_current_line_region


class Bookmark:
    def __init__(self, uid, name, project_path, active_view):
        self.uid = uid
        self.name = name
        self.file_path = active_view.file_name()
        self.project_path = project_path
        self.region = get_current_line_region(active_view)
        self.line_str = active_view.substr(self.region)

        cursor_pos = active_view.sel()[0].begin()
        self.line_number = active_view.rowcol(cursor_pos)[0]

    # the bookmark is associated with the current view
    def is_my_view(self, view):
        return view and (self.file_path == view.file_name())

    def update_data(self, my_view):
        """
        Updates the bookmark's data
        1) moved region to cover whole line
        3) updates the current line string
        """
        regions = my_view.get_regions(self.uid)

        # the region is not loaded yet
        if len(regions) == 0:
            return

        lines = my_view.split_by_newlines(regions[0])
        self.region = lines[0]
        self.line_str = my_view.substr(self.region)
