# Copyright (C) 2017 Tom Hartill
#
# ThemedIconChooserAdapter.py - Adapters for use with glade.
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

import glade
from ThemedIconChooser import IconChooserButton,\
    IconChooserComboBox, IconChooserDialog

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

#class IconChooserButtonAdapter (get_adaptor_for_type('GtkButton')):
#    __gtype_name__ = 'IconChooserButtonAdapter'
#
#    def do_add(self, obj, child):
#        """Called to add a child to the widget"""
#        obj.frame.add(child)
#
#    def do_child_get_property(self, obj, child, prop):
#        """Called to retrieve a property value"""
#        if prop in ['expand', 'fill']:
#            return True
#        elif prop == 'padding':
#            return 0
#        elif prop == 'position':
#            return 0
#        elif prop == 'pack-type':
#            return Gtk.PackType.START
#        return True
#
#    def do_child_set_property(self, obj, child, prop, val):
#        """Called to set a property value"""
#        if prop in ['expand', 'fill', 'padding', 'pack-type']:
#            pass
#
#    def do_get_children(self, obj):
#        """Called when glade wants the children of a widget"""
#        return obj.frame.get_children()
#
#    def do_remove(self, obj, child):
#        """Called to remove a child from our widget"""
#        obj.frame.remove(child)
#
#    def do_replace_child(self, obj, old, new):
#        """Called to replace the child of our widget.
#
#        Note that this is what is called by glade when you delete,
#        or cut a widget since it actually replaces the widget with a
#        GladePlaceholder
#        """
#        obj.frame.remove(old)
#        obj.frame.add(new)