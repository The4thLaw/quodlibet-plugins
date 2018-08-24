# Copyright (C) 2018 Xavier Dalem
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# This plugin allows the user to filter a playlist randomly so that it fits on
# e.g. a removable device or media player

import random, sys

from gi.repository import Gtk

from quodlibet import _, app
from quodlibet.plugins.playlist import PlaylistPlugin
from quodlibet.qltk import Icons
from quodlibet.qltk.msg import Message

class PlaylistSize(PlaylistPlugin):
    PLUGIN_ID = 'playlistsizetruncaterandom'
    PLUGIN_NAME = _('Truncate playlists to size')
    PLUGIN_DESC = _('Truncates a playlist to a given size in MB by removing songs at random')
    PLUGIN_ICON = Icons.EDIT_CLEAR
    REQUIRES_ACTION = True

    def plugin_handles(self, playlists):
        return len(playlists) == 1

    def plugin_playlist(self, playlist):
        size = 0
        for s in playlist.songs:
            size += s['~#filesize']
        
        # Create a dialog.
        sizeSelectDlg = Gtk.Dialog(title=_('Select a size'),
                         parent=app.window,
                         flags=(Gtk.DialogFlags.MODAL |
                                Gtk.DialogFlags.DESTROY_WITH_PARENT))
        sizeSelectDlg.add_button(_('_Cancel'), Gtk.ResponseType.REJECT)
        sizeSelectDlg.add_button(_('_Apply'), Gtk.ResponseType.APPLY)
        sizeSelectDlg.set_default_response(Gtk.ResponseType.APPLY)
        
        sizeSelectDlg.vbox.set_spacing(5)
        label = Gtk.Label(_('Enter a maximum size in MB'))
        sizeSelectDlg.vbox.add(label)
        maxSize = Gtk.SpinButton()
        maxSize.set_numeric(True)
        maxSize.set_adjustment(Gtk.Adjustment(int(size/1024/1024), 1, sys.maxsize, 1, 1))
        sizeSelectDlg.vbox.add(maxSize)
        
        sizeSelectDlg.show_all()
        
        # Only operate if apply is pressed.
        if sizeSelectDlg.run() == Gtk.ResponseType.APPLY:
            sizeSelectDlg.destroy()
            
            currentSize = size;
            desiredSize = int(maxSize.get_value() * 1024 * 1024)
            
            while desiredSize < currentSize:
                #dialog3 = Message(Gtk.MessageType.INFO, app.window, playlist.name, _('Current: ') + str(currentSize) + ' ' + _('Desired: ') + str(desiredSize))
                #dialog3.run()
                song = random.choice(playlist.songs)
                #dialog4 = Message(Gtk.MessageType.INFO, app.window, playlist.name, _('Song: ') + song['title'])
                #dialog4.run()
                playlist.remove_songs([song], True)
                currentSize -= song['~#filesize']
            return True
        else:
            sizeSelectDlg.destroy()

        return False
