# Copyright (C) 2017 Tom Hartill
#
# Demo.py - A simple demo of the widgets provided by ThemedIconChooser.
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

import ThemedIconChooser

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class Demo:
    def __init__(self):
        self.window = Gtk.Window()
        self.window.set_icon_name('gtk-search')
        self.window.set_title('Demo')

        box = Gtk.Box()
        box.set_margin_bottom(8)
        box.set_margin_left(8)
        box.set_margin_right(8)
        box.set_margin_top(8)
        box.set_orientation(Gtk.Orientation.VERTICAL)
        box.set_spacing(8)

        # Create a button to show a IconChooserDialog

        icon_chooser_dialog = Gtk.Button('Show Dialog')
        icon_chooser_dialog.connect('clicked', self.show_dialog)
        box.pack_start(icon_chooser_dialog, True, True, 0)

        # Create an IconChooserButton
        icon_chooser_button = ThemedIconChooser.IconChooserButton()
        icon_chooser_button.set_context_filter(['Emblems', 'Emotes'])
        icon_chooser_button.set_icon_size(16)
        box.pack_start(icon_chooser_button, True, True, 0)

        # Create an IconChooserComboBox to search for Steam game icons
        icon_chooser_combo = ThemedIconChooser.IconChooserComboBox()
        icon_chooser_combo.set_context_filter(['Applications'])
        icon_chooser_combo.set_search_term('git')
        icon_chooser_combo.connect('changed', self.test)
        icon_chooser_combo.populate()
        box.pack_start(icon_chooser_combo, True, True, 0)

        # Start
        self.window.add(box)
        self.window.connect('destroy', Gtk.main_quit)
        self.window.show_all()
        Gtk.main()

    def show_dialog(self, button):
        dialog = ThemedIconChooser.IconChooserDialog()
        dialog.set_transient_for(self.window)
        dialog.run()
        dialog.destroy()

    def test(self, one):
        print(one.get_selected_icon_name())

if __name__ == '__main__':
    Demo()
