# Copyright (C) 2017 Tom Hartill
#
# ThemedIconChooser.py - A set of GTK+ 3 widgets for selecting themed icons.
#
# ThemedIconChooser is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 3 of the License, or (at your option) any
# later version.
#
# ThemedIconChooser is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# ThemedIconChooser; if not, see http://www.gnu.org/licenses/.
#
# An up to date version can be found at:
# https://github.com/Tomha/GtkThemedIconChooser

import re
from threading import Thread

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, GObject, Gtk, Pango


class IconChooserDialog(Gtk.Dialog):
    # TODO: Not all memory created by the dialog seems to be released.
    """GTK+ 3 Dialog to allow selection of a themed icon.

    NOTE: Displaying the icons involves showing potentially 1000s of widgets.
    This has to be done in the main thread and will cause the dialog to
    freeze momentarily as all widgets are showing. Initial loading of icons is
    done asynchronously to reduce this freeze time. This should have minimal
    impact most of the time, and can be limited by restricting the number of
    icons that need to be shown via a search term to filter out some icons.
    """
    def __init__(self):
        super().__init__()
        GLib.threads_init()

        self._context_filter_list = []
        self._icon_size = 32
        self._icon_theme = None
        self._search_term = ''
        self._selected_context = ''
        self._selected_icon = ''
        self._use_regex = False

        self._context_store = Gtk.ListStore(str)
        self._text_renderer = Gtk.CellRendererText()

        self.set_default_size(500, 500)
        self.set_icon_name('gtk-search')
        self.set_title('Choose An Icon')

        # Widgets start here
        icon_context_label = Gtk.Label('Icon Context:')
        icon_context_label.set_width_chars(11)

        self.icon_context_combo = Gtk.ComboBox()
        self.icon_context_combo.set_model(self._context_store)
        self.icon_context_combo.pack_start(self._text_renderer, True)
        self.icon_context_combo.add_attribute(self._text_renderer, "text", 0)

        icon_context_box = Gtk.Box()
        icon_context_box.set_spacing(4)
        icon_context_box.pack_start(icon_context_label, False, False, 0)
        icon_context_box.pack_start(self.icon_context_combo, True, True, 0)

        filter_label = Gtk.Label('Search Term:')
        filter_label.set_width_chars(11)

        self.filter_entry = Gtk.Entry()

        filter_clear_button = Gtk.Button.new_from_icon_name('gtk-clear',
                                                            Gtk.IconSize.MENU)

        filter_box = Gtk.Box()
        filter_box.set_spacing(4)
        filter_box.pack_start(filter_label, False, False, 0)
        filter_box.pack_start(self.filter_entry, True, True, 0)
        filter_box.pack_start(filter_clear_button, False, False, 0)

        self.icon_box = Gtk.FlowBox()
        self.icon_box.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.icon_box.set_column_spacing(8)
        self.icon_box.set_row_spacing(8)
        self.icon_box.set_homogeneous(True)
        self.icon_box.set_valign(Gtk.Align.START)

        self.scroller = Gtk.ScrolledWindow()
        self.scroller.add(self.icon_box)

        # A slight hack to get the theme's background color for widgets.
        context = self.filter_entry.get_style_context()
        background_color = context.get_background_color(Gtk.StateType.NORMAL)
        self.icon_box_frame = Gtk.Frame()
        self.icon_box_frame.override_background_color(Gtk.StateFlags.NORMAL,
                                                      background_color)
        self.icon_box_frame.add(self.scroller)

        # Spinner
        self.spinner = Gtk.Spinner()
        self.spinner.set_size_request(48, 48)
        self.spinner.set_hexpand(False)
        self.spinner.set_vexpand(False)
        self.spinner.set_halign(Gtk.Align.CENTER)
        self.spinner.set_valign(Gtk.Align.CENTER)

        # Pack widgets in dialog
        content_box = self.get_content_area()
        content_box.set_margin_left(8)
        content_box.set_margin_right(8)
        content_box.set_margin_top(8)
        content_box.set_margin_bottom(8)
        content_box.set_spacing(8)
        content_box.pack_start(icon_context_box, False, False, 0)
        content_box.pack_start(filter_box, False, False, 0)
        content_box.pack_start(self.icon_box_frame, True, True, 0)

        # Set dialog buttons
        button_box = self.get_action_area()
        button_box.set_spacing(4)
        self._ok_button = self.add_button(Gtk.STOCK_OK, 1)
        self.add_button(Gtk.STOCK_CANCEL, 0)

        # Connect signals
        self.icon_context_combo.connect('changed', self._on_context_changed)
        self.filter_entry.connect('changed', self._filter_icons)
        filter_clear_button.connect('clicked', lambda button:
                                    self.filter_entry.set_text(''))
        self.icon_box.connect('selected-children-changed',
                              self._on_icon_selected)

    def _create_icon_previews(self, icon_name_list, icon_size):
        """Create icon previews for icon box. Intended to be run in new thread.

        This only creates previews and adds them to the icon flow box, but it
        will not show them. This is done by calling _display_icon_previews,
        which GLib.idle_add since this should be run in a new thread to
        prevent unnecessary UI delays.
        """
        for icon in icon_name_list:
            flow_child = Gtk.FlowBoxChild()
            flow_child.add(_IconPreview(icon, icon_size))
            flow_child.connect('activate', self._on_icon_preview_selected)
            GLib.idle_add(self.icon_box.insert, flow_child, -1)
        GLib.idle_add(self._display_icon_previews)

    def _display_icon_previews(self):
        """Display icons and clean up after _create_icon_previews is run.

        WARNING: This must be run from the main thread, however show_all can
        take a noticeable amount of time, so the dialog will freeze momentarily
        as this runs if there are many icons to display. This is not avoidable
        to my knowledge.
        """
        self.icon_context_combo.set_sensitive(True)
        self.icon_box_frame.remove(self.icon_box_frame.get_children()[0])
        self.icon_box_frame.add(self.scroller)
        self.spinner.stop()
        self.scroller.show_all()

        if self.filter_entry.get_text():
            self._filter_icons(self.filter_entry)
            self.filter_entry.set_position(len(self.filter_entry.get_text()))
        else:
            self.icon_box.show_all()

    def _filter_icons(self, entry):
        """Filter icons based on search term, used when search term changes.

        If use_regex is True, the provided string will be used as the pattern
        for a regex match.

        If use_regex is False, icon names will be set to lower case and have
        underscores and dashes replaced with spaces, then it is checked if the
        lower case filter term is a substring of any icon name.
        """
        self._search_term = entry.get_text()
        if self._search_term == '':
            for icon in self.icon_box.get_children():
                icon.show()
        else:
            for icon in self.icon_box.get_children():
                if self._use_regex:
                    if re.search(self._search_term, icon):
                        icon.show()
                    else:
                        icon.hide()
                else:
                    name = icon.get_children()[0].get_name().lower()\
                        .replace('-', ' ').replace('_', ' ')
                    if self._search_term.lower() in name:
                        icon.show()
                    else:
                        icon.hide()

    def _on_context_changed(self, combobox):
        """Display icons for a context, used when context changes."""

        self._ok_button.set_sensitive(False)
        self._selected_icon = None
        self._selected_context = \
            self._context_store.get_value(
                self.icon_context_combo.get_active_iter(), 0)

        current_icons = self._icon_theme.list_icons(self._selected_context)
        current_icons.sort()

        for child in self.icon_box.get_children():
            child.destroy()

        # Place a spinner in the icon section while icons are loaded.
        self.icon_box_frame.remove(self.icon_box_frame.get_children()[0])
        self.icon_box_frame.add(self.spinner)
        self.spinner.start()
        self.icon_context_combo.set_sensitive(False)
        thread = Thread(target=self._create_icon_previews,
                        args=(current_icons, self._icon_size))
        thread.setDaemon(True)
        thread.start()

    def _on_icon_preview_selected(self, preview):
        """Emulate OK button press. used when an icon preview is activated."""
        self.response(1)

    def _on_icon_selected(self, flowbox):
        """Sets the selected icon, used when dialog selection changes."""
        selection = flowbox.get_selected_children()
        if not selection:
            self._selected_icon = None
        else:
            self._selected_icon = selection[0].get_children()[0].get_name()
            self._ok_button.set_sensitive(True)

    def get_context_filter(self):
        """Get the list of icon contexts to allow selection from."""
        return self._context_filter_list

    def get_search_term(self):
        """Get the string used to search for icons."""
        return self._search_term

    def get_icon_size(self):
        """Get the pixel size of icons to display."""
        return self._icon_size

    def get_selected_context(self):
        """Get the icon context currently active in the dialog."""
        return self._selected_context

    def get_selected_icon_name(self):
        """Get the name if the icon currently selected in the dialog."""
        return self._selected_icon

    def get_use_regex(self):
        """Get whether or not regex terms are used to search for icons."""
        return self._use_regex

    def run(self):
        """Run dialog to load icon theme and display previews for selections.

        Loads a new icon theme, gets then filters available contexts, and
        filters/displays icon previews for the first (alphabetically) context.

        Don't forget to call destroy() or hide() after run completes.

        :return: None
        """
        self._icon_theme = Gtk.IconTheme.get_default()
        if self._context_filter_list:
            used_contexts = []
            for context in self._icon_theme.list_contexts():
                if context in self._context_filter_list:
                    used_contexts += [context]
            used_contexts.sort()
        else:
            used_contexts = self._icon_theme.list_contexts()
            used_contexts.sort()

        self._context_store.clear()
        for context in used_contexts:
            self._context_store.append([context])
        self.icon_context_combo.set_active(0)
        self._ok_button.set_sensitive(False)

        if self._search_term:
            self.filter_entry.set_text(self._search_term)

        self.show_all()
        if super().run() == 1:
            return self._selected_icon
        return None

    def set_context_filter(self, context_list):
        """Set the list of icon contexts to allow selection from.

        Icon contexts can be found using:
        Gtk.IconTheme.get_default().list_contexts()

        Dialog will not reflect changes to filter list once it is run.
        """
        if not type(context_list) == list:
            raise TypeError('must be type list, not ' +
                            type(context_list).__name__)
        self._context_filter_list = list(set(context_list))

    def set_icon_size(self, size):
        """Set the pixel size of icons to display.

        Dialog will not reflect changes to icon size once it is run.
        """
        if not type(size) == int:
            raise TypeError('must be type int, not ' +
                            type(size).__name__)
        self._icon_size = size

    def set_search_term(self, filter_term):
        """Set the string used to search for icons.

        If use_regex is True, the provided string will be used as the pattern
        for a regex match.

        If use_regex is False, icon names will be set to lower case and have
        underscores and dashes replaced with spaces, then it is checked if the
        lower case filter term is a substring of any icon name.

        Dialog will not reflect changes to search term once it is run.
        """
        if not type(filter_term) == str:
            raise TypeError('must be type str, not ' +
                            type(filter_term).__name__)
        self._search_term = filter_term

    def set_use_regex(self, use_regex):
        """Set whether or not regex terms are used to search for icons.

        Dialog will not reflect changes to regex use once it is run.
        """
        if not type(use_regex) == bool:
            raise TypeError('must be type bool, not ' +
                            type(use_regex).__name__)
        self._use_regex = use_regex


class IconChooserButton(Gtk.Button):
    """GTK + 3 button to open dialog allowing selection of a themed icon.

    The selected icon is emited via the 'icon_selected' signal once the dialog
    is closed. It will be either the icon name, or None if icon wasnt selected.

    NOTE: Icon preview in dialog and button may differ as icons can have
    a different appearance at different sizes, and the dialog by default uses
    a larger size (32px) than the button (16px). set_dialog_icon_size(16) can
    be used to get dialog to display the same icon that will be shown on the
    button.

    NOTE: See the IconChooserDialog for a note on UI freezing while the dialog
    loads icons.
    """
    def __init__(self):
        super().__init__()

        self._dialog_context_filter_list = []
        self._dialog_icon_size = 32
        self._dialog_search_term = ''
        self._dialog_use_regex = False
        self._selected_icon = None

        # Register a custom icon_selected signal for once dialog closes.
        GObject.type_register(IconChooserButton)
        GObject.signal_new('icon_selected',
                           IconChooserButton,
                           GObject.SIGNAL_RUN_FIRST,
                           GObject.TYPE_NONE,
                           [GObject.TYPE_STRING])

        self._icon = Gtk.Image.new_from_icon_name('gtk-search',
                                                  Gtk.IconSize.MENU)
        self._icon.set_margin_left(2)

        open_icon = Gtk.Image.new_from_icon_name('document-open-symbolic',
                                                 Gtk.IconSize.MENU)
        self._label = Gtk.Label('(Choose An Icon)')
        self._label.set_hexpand(True)
        self._label.set_halign(Gtk.Align.START)
        self._label.set_ellipsize(Pango.EllipsizeMode.END)

        box = Gtk.Box()
        box.set_spacing(4)
        box.pack_start(self._icon, False, False, 0)
        box.pack_start(self._label, False, True, 0)
        box.pack_start(open_icon, False, False, 2)

        self.add(box)
        self.connect('clicked', self._show_dialog)

    def get_context_filter(self):
        """Get the list of icon contexts to allow selection from."""
        return self._dialog_context_filter_list

    def get_icon_size(self):
        """Get the pixel size of icons to display."""
        return self._dialog_icon_size

    def get_search_term(self):
        """Get the string used to search for icons."""
        return self._dialog_search_term

    def get_selected_icon_name(self):
        """Get the name if the icon selected in the dialog."""
        return self._selected_icon

    def get_use_regex(self):
        """Get whether or not regex terms are used to search for icons."""
        return self._dialog_use_use_regex

    def set_context_filter(self, context_list):
        """Set the list of icon contexts to allow selection from.

        Icon contexts can be found using:
        Gtk.IconTheme.get_default().list_contexts()

        Dialog will not reflect changes to filter list once button is clicked.
        """
        if not type(context_list) == list:
            raise TypeError('must be type list, not ' +
                            type(context_list).__name__)
        self._dialog_context_filter_list = list(set(context_list))

    def set_icon_size(self, size):
        """Set the pixel size of icons to display.

        Dialog will not reflect changes to icon size once button is clicked.
        """
        if not type(size) == int:
            raise TypeError('must be type int, not ' +
                            type(size).__name__)
        self._dialog_icon_size = size

    def set_search_term(self, filter_term):
        """Set the string used to search for icons.

        If use_regex is True, the provided string will be used as the pattern
        for a regex match.

        If use_regex is False, icon names will be set to lower case and have
        underscores and dashes replaced with spaces, then it is checked if the
        lower case filter term is a substring of any icon name.

        Dialog will not reflect changes to search term once it is run.
        """
        if not type(filter_term) == str:
            raise TypeError('must be type str, not ' +
                            type(filter_term).__name__)
        self._dialog_search_term = filter_term

    def set_use_regex(self, use_regex):
        """Set whether or not regex terms are used to search for icons.

        Dialog will not reflect changes to regex use once it is run.
        """
        if not type(use_regex) == bool:
            raise TypeError('must be type bool, not ' +
                            type(use_regex).__name__)
        self._dialog_use_regex = use_regex

    def _show_dialog(self, button):
        """Shows an icon chooser dialog and emits result with icon_selected."""
        dialog = IconChooserDialog()
        dialog.set_transient_for(self.get_toplevel())
        dialog.set_context_filter(self._dialog_context_filter_list)
        dialog.set_icon_size(self._dialog_icon_size)
        dialog.set_search_term(self._dialog_search_term)
        dialog.set_use_regex(self._dialog_use_regex)
        self._selected_icon = dialog.run()
        dialog.destroy()

        if self._selected_icon:
            self._icon.set_from_icon_name(self._selected_icon,
                                          Gtk.IconSize.MENU)
            self._label.set_text(self._selected_icon)
        self.emit('icon_selected', self._selected_icon)


class IconChooserComboBox(Gtk.ComboBox):
    """GTK+ 3 ComboBox allowing selection of a themed icon.

    Population of the combobox can take several seconds or more, so is not done
    on instantiation so you have more control over when this delay occurs.

    WARNING: It is strongly advised against using this without context filters
    and/or an icon search term to severely cut down on the number of icons to
    be displayed.

    I have tried to filter icons and populate the combobox asynchronously, but
    have thus far been unsuccessful at making a difference to the delay. Most
    of the delay comes from populating the combobox list store and calling
    show_all to display all entries in the combobox, and this must be done in
    the main thread so it seems this is simply unavoidable under GTK.
    """
    def __init__(self):
        super().__init__()

        self._context_filter_list = []
        self._search_term = ''
        self._use_regex = False

        pixbuf_renderer = Gtk.CellRendererPixbuf()
        text_renderer = Gtk.CellRendererText()

        self._icon_store = Gtk.ListStore(str, str)
        self._icon_store.set_sort_column_id(0, Gtk.SortType.ASCENDING)

        self.set_model(self._icon_store)
        self.pack_start(pixbuf_renderer, True)
        self.add_attribute(pixbuf_renderer, "icon_name", 1)
        self.pack_start(text_renderer, True)
        self.add_attribute(text_renderer, "text", 0)

    def get_context_filter(self):
        """Get the list of icon contexts from which to select icons."""
        return self._context_filter_list

    def get_search_term(self):
        """Get the string used to filter icons."""
        return self._search_term

    def get_selected_icon_name(self):
        """Get the name if the icon currently selected in the combo box."""
        selection = self._icon_store.get_value(self.get_active_iter(), 0)
        if selection == '(Choose An Icon)':
            return None
        else:
            return selection

    def get_use_regex(self):
        """Get whether or not regex terms are used to search for icons."""
        return self._use_regex

    def populate(self):
        """Populate the combo box with icons matching any given context/filter.

        WARNING: Adding icons to the combo box and show()ing them is a costly
        operation which must be done in the main thread, so if you have no
        context filter or icon search term set OR either of the above but they
        are too broad, the large number of icons will cause your main UI thread
        to freeze for several seconds or more.

        This is intended only for use in situations where the number of icons
        to select from is quite limited.
        """
        if not self._context_filter_list and not self._search_term:
            print("WARNING: Populating IconChooserComboBox without any"
                  " filters set! This will probably freeze the main thread for"
                  " several seconds and is NOT recommended.")

        # Get icons by context
        unfiltered_icons = []
        icon_theme = Gtk.IconTheme.get_default()
        if self._context_filter_list:
            for context in self._context_filter_list:
                if context in icon_theme.list_contexts():
                    unfiltered_icons += icon_theme.list_icons(context)
        else:
            for context in icon_theme.list_contexts():
                unfiltered_icons += icon_theme.list_icons(context)

        # Filter icons
        filtered_icons = []
        if self._search_term == '':
            for icon in unfiltered_icons:
                filtered_icons += [icon]
        else:
            for icon in unfiltered_icons:
                if self._use_regex:
                    if re.search(self._search_term, icon):
                        filtered_icons += [icon]
                else:
                    name = icon.lower().replace('-', ' ').replace('_', ' ')
                    if self._search_term.lower() in name:
                        filtered_icons += [icon]

        if len(filtered_icons) > 200:
            print("WARNING: Your IconChooserComboBox is trying to display over"
                  " 200 icons. This is likely to cause unwanted  UI delays."
                  " Consider using an icon chooser button, or limiting the"
                  " search further.")

        # Here is the time-consuming bit
        self._icon_store.clear()
        self._icon_store.append(['(Choose An Icon)', 'gtk-search'])
        for icon in filtered_icons:
            self._icon_store.append([icon, icon])
        self.set_active(0)
        self.show_all()

    def set_context_filter(self, context_list):
        """Set the list of icon contexts to allow search for icons.

        Icon contexts can be found using:
        Gtk.IconTheme.get_default().list_contexts()

        Combobox will not reflect changes to filter list once it is run.
        """
        if not type(context_list) == list:
            raise TypeError('must be type list, not ' +
                            type(context_list).__name__)
        self._context_filter_list = list(set(context_list))

    def set_search_term(self, filter_term):
        """Set the string used to search for icons.

        If use_regex is True, the provided string will be used as the pattern
        for a regex match.

        If use_regex is False, icon names will be set to lower case and have
        underscores and dashes replaced with spaces, then it is checked if the
        lower case filter term is a substring of any icon name.

        Combobox will not reflect changes to search term once it is run.
        """
        if not type(filter_term) == str:
            raise TypeError('must be type str, not ' +
                            type(filter_term).__name__)
        self._search_term = filter_term

    def set_use_regex(self, use_regex):
        """Set whether or not regex terms are used to search for icons.

        Combobox will not reflect changes to regex use once it is run.
        """
        if not type(use_regex) == bool:
            raise TypeError('must be type bool, not ' +
                            type(use_regex).__name__)
        self._use_regex = use_regex


class _IconPreview(Gtk.Box):
    """Creates a preview box for icons containing the icon and its name."""
    def __init__(self, name, size):
        super().__init__()
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(2)

        self._icon_name = name
        self._display_name = name.replace('-', ' ').replace('_', ' ')
        self._icon_size = size

        icon = Gtk.Image.new_from_icon_name(name, Gtk.IconSize.DIALOG)
        # Gtk.Image.new_from_icon_name seems to sometimes ignore the set size,
        #   leading to inconsistent icon sizes. Solution is to force a size
        #   using set_pixel_size.
        icon.set_pixel_size(size)
        icon.set_tooltip_text(self._icon_name)

        label = Gtk.Label(self._display_name)
        label.set_justify(Gtk.Justification.CENTER)
        label.set_lines(3)
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_max_width_chars(8)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_yalign(0.5)

        self.pack_start(icon, False, False, 0)
        self.pack_start(label, False, False, 0)

    def get_name(self):
        """Get the name of the icon."""
        return self._icon_name
