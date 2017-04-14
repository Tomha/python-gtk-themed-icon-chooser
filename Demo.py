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
        self.window.set_icon_name("gtk-search")
        self.window.set_title("Demo")

        box = Gtk.Box()
        box.set_margin_bottom(8)
        box.set_margin_left(8)
        box.set_margin_right(8)
        box.set_margin_top(8)
        box.set_orientation(Gtk.Orientation.VERTICAL)
        box.set_spacing(8)

        # Create a button to show a IconChooserDialog
        icon_chooser_dialog = Gtk.Button("Show Dialog")
        icon_chooser_dialog.connect("clicked", self.show_dialog)
        box.pack_start(icon_chooser_dialog, True, True, 0)

        # Create an IconChooserButton
        icon_chooser_button = ThemedIconChooser.IconChooserButton()
        icon_chooser_button.set_icon_contexts(["Applications"])
        icon_chooser_button.set_filter_term("steam")
        icon_chooser_button.set_icon_size(16)
        icon_chooser_button.connect("clicked", print_selection)
        box.pack_start(icon_chooser_button, True, True, 0)

        # Create an IconChooserComboBox
        icon_chooser_combo = ThemedIconChooser.IconChooserComboBox()
        icon_chooser_combo.set_icon_contexts(["Applications"])
        icon_chooser_combo.set_filter_term("git")
        icon_chooser_combo.populate()
        icon_chooser_combo.connect("changed", print_selection)
        box.pack_start(icon_chooser_combo, True, True, 0)

        # Start
        self.window.add(box)
        self.window.connect("destroy", Gtk.main_quit)
        self.window.show_all()
        Gtk.main()

    def show_dialog(self, button):
        dialog = ThemedIconChooser.IconChooserDialog()
        dialog.set_transient_for(self.window)
        selection = dialog.run()
        dialog.destroy()
        if not selection:
            print("No icon was selected.")
        else:
            print("{0} was selected.".format(selection))


def print_selection(widget):
    selection = widget.get_selected_icon_name()
    if not selection:
        print("No icon was selected.")
    else:
        print("{0} was selected.".format(selection))

if __name__ == "__main__":
    Demo()
