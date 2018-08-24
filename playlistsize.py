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

# This plugin is more of a demo plugin to show the size of a selected playlist.
# QuodLibet already shows this natively

from gi.repository import Gtk

from quodlibet import _, app
from quodlibet.plugins.playlist import PlaylistPlugin
from quodlibet.qltk.msg import Message

class PlaylistSize(PlaylistPlugin):
    PLUGIN_ID = 'playlistsize'
    PLUGIN_NAME = _('Compute playlist size')
    PLUGIN_DESC = _('Computes the size of the selected playlists, in MB')
    PLUGIN_ICON = 'document-properties'

    def plugin_handles(self, playlists):
        return len(playlists) == 1

    def plugin_playlist(self, playlist):
        size = 0
        for s in playlist.songs:
            size += s['~#filesize']
        
        sizeInMB = str(int(size / 1024 / 1024))
        dialog = Message(Gtk.MessageType.INFO, app.window, playlist.name, _('The total size in MB is: ') + sizeInMB)
        dialog.run()

        return False