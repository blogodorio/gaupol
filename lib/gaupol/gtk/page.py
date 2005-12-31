# Copyright (C) 2005 Osmo Salomaa
#
# This file is part of Gaupol.
#
# Gaupol is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Gaupol is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Gaupol; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


"""User interface for a single project."""

try:
    from psyco.classes import *
except ImportError:
    pass

import os

import gobject
import gtk
import pango

from gaupol.base.project     import Project
from gaupol.constants        import Format, Mode
from gaupol.gtk.colconstants import *
from gaupol.gtk.util         import config, gui
from gaupol.gtk.view         import View


class Page(gobject.GObject):

    """User interface for a single project."""

    __gsignals__ = {
        'close-button-clicked': (
            gobject.SIGNAL_RUN_LAST,
            None,
            ()
        ),
    }

    def __init__(self, counter=0):

        gobject.GObject.__init__(self)

        if config.editor.limit_undo:
            undo_limit = config.editor.undo_levels
        else:
            undo_limit = None

        self.project   = Project(config.editor.framerate, undo_limit)
        self.untitle   = _('Untitled %d') % counter
        self.edit_mode = config.editor.mode

        self.view           = View(self.edit_mode)
        self.tab_label      = None
        self.tab_menu_label = None
        self.tooltips       = gtk.Tooltips()

    def init_tab_widget(self):
        """Initialize and return the notebook tab widget."""

        title = self.get_main_basename()

        # Tab label
        self.tab_label = gtk.Label(title)
        self.tab_label.props.xalign = 0
        self.tab_label.set_ellipsize(pango.ELLIPSIZE_MIDDLE)
        self.tab_label.set_max_width_chars(24)

        # Event box for tooltip
        event_box = gtk.EventBox()
        event_box.add(self.tab_label)
        self.tooltips.set_tip(event_box, self.get_main_filename())

        # Tab close image
        image = gtk.image_new_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
        width, height = image.size_request()

        # Tab close button
        button = gtk.Button()
        button.add(image)
        button.set_relief(gtk.RELIEF_NONE)
        button.set_size_request(width + 2, height + 2)
        button.connect('clicked', self._on_close_button_clicked)

        # Tab horizontal box
        tab_widget = gtk.HBox(False, 4)
        tab_widget.pack_start(event_box, True , True , 0)
        tab_widget.pack_start(button   , False, False, 0)
        tab_widget.show_all()

        # Tab menu label
        self.tab_menu_label = gtk.Label(title)
        self.tab_menu_label.props.xalign = 0

        return tab_widget

    def get_main_basename(self):
        """Get basename of main document."""

        try:
            return os.path.basename(self.project.main_file.path)
        except AttributeError:
            return self.untitle

    def get_main_corename(self):
        """Get basename of main document without extension."""

        try:
            basename = os.path.basename(self.project.main_file.path)
            format = self.project.main_file.format
        except AttributeError:
            return self.untitle

        extension = Format.extensions[format]
        if basename.endswith(extension):
            return basename[0:-len(extension)]
        else:
            return basename

    def get_main_filename(self):
        """Get filename of main document."""

        try:
            return self.project.main_file.path
        except AttributeError:
            return self.untitle

    def _get_timings(self):
        """Get project.times or project.frames depending on edit mode."""

        if self.edit_mode == Mode.TIME:
            return self.project.times
        elif self.edit_mode == Mode.FRAME:
            return self.project.frames

    def get_translation_basename(self):
        """Get basename of translation document."""

        if self.project.tran_file is not None:
            return os.path.basename(self.project.tran_file.path)
        elif self.project.main_file is not None:
            # Translators: Suggested translation file basename,
            # "<main basename> translation".
            return _('%s translation') % self.get_main_corename()
        else:
            # Translators: Suggested translation file basename,
            # "<main basename> translation".
            return _('%s translation') % self.untitle

    def get_translation_corename(self):
        """Get basename of translation document without extension."""

        try:
            basename = os.path.basename(self.project.tran_file.path)
            format = self.project.tran_file.format
        except AttributeError:
            return self.get_translation_basename()

        extension = Format.extensions[format]
        if basename.endswith(extension):
            return basename[0:-len(extension)]
        else:
            return basename

    def _on_close_button_clicked(self, *args):
        """Emit signal that the notebook tab close button has been clicked."""

        self.emit('close-button-clicked')

    def reload_after_row(self, row):
        """Reload view after row."""

        store      = self.view.get_model()
        timings    = self._get_timings()
        main_texts = self.project.main_texts
        tran_texts = self.project.tran_texts

        # Selection must be cleared before removing rows to avoid selection
        # constantly changing and emitting the "changed" signal if the row
        # being removed was selected.
        selected_rows = self.view.get_selected_rows()
        self.view.select_rows([])

        while len(store) > row:
            store.remove(store.get_iter(row))
        for i in range(row, len(self.project.times)):
            store.append([i + 1] + timings[i] + [main_texts[i], tran_texts[i]])

        # Reselect all rows that still exist.
        for i in reversed(range(len(selected_rows))):
            if selected_rows[i] >= len(self.project.times):
                selected_rows.pop(i)
        self.view.select_rows(selected_rows)

    def reload_all(self):
        """
        Reload all data in the view.

        Possible selection, focus and scroll position are lost.
        """
        store = self.view.get_model()
        self.view.set_model(None)
        store.clear()

        timings    = self._get_timings()
        main_texts = self.project.main_texts
        tran_texts = self.project.tran_texts

        for i in range(len(self.project.times)):
            store.append([i + 1] + timings[i] + [main_texts[i], tran_texts[i]])

        self.view.set_model(store)

    def reload_between_rows(self, row_x, row_y):
        """Reload view by full rows between row_x and row_y."""

        first_row = min(row_x, row_y)
        last_row  = max(row_x, row_y)

        rows = range(first_row, last_row + 1)
        self.reload_rows(rows)

    def reload_columns(self, cols, rows=None):
        """Reload view column by column."""

        store = self.view.get_model()
        rows  = rows or range(len(store))

        for col in cols:

            if col == NO:
                for row in rows:
                    store[row][col] = row + 1

            elif col in (SHOW, HIDE, DURN):
                timings  = self._get_timings()
                base_col = col - 1
                for row in rows:
                    store[row][col] = timings[row][base_col]

            elif col == MTXT:
                main_texts = self.project.main_texts
                for row in rows:
                    store[row][col] = main_texts[row]

            elif col == TTXT:
                tran_texts = self.project.tran_texts
                for row in rows:
                    store[row][col] = tran_texts[row]

    def reload_row(self, row):
        """Reload view in full row."""

        self.reload_rows([row])

    def reload_rows(self, rows):
        """Reload view by full rows."""

        store      = self.view.get_model()
        timings    = self._get_timings()
        main_texts = self.project.main_texts
        tran_texts = self.project.tran_texts

        for row in rows:
            store[row] = [row + 1] + timings[row] + \
                         [main_texts[row], tran_texts[row]]

    def update_tab_labels(self):
        """
        Update text in the notebook tab labels.

        Return tab label title.
        """
        title = self.get_main_basename()
        if self.project.main_changed:
            title = '*' + title
        elif self.project.tran_active and self.project.tran_changed:
            title = '*' + title

        self.tab_label.set_text(title)
        self.tab_menu_label.set_text(title)

        event_box = gui.get_event_box(self.tab_label)
        self.tooltips.set_tip(event_box, self.get_main_filename())

        return title