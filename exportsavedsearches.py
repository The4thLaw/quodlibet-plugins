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

# Inspired by https://gist.github.com/Tamriel/204ee6e3fe84e7450d2a71d6127f34eb

import glob
import os
from os.path import relpath
from gi.repository import Gtk
from quodlibet import _, app, config, get_user_dir, qltk
from quodlibet.library import SongLibrary
from quodlibet.plugins import PluginConfigMixin
from quodlibet.plugins.events import EventPlugin
from quodlibet.qltk import Icons
from quodlibet.qltk.ccb import ConfigCheckButton
from quodlibet.query import Query
from quodlibet.util.path import get_home_dir

class ExportSavedSearches(EventPlugin, PluginConfigMixin):
    PLUGIN_ID = 'ExportSavedSearches'
    PLUGIN_NAME = _('Export saved searches')
    PLUGIN_DESC = _('Exports saved searches to M3U playlists.')
    PLUGIN_ICON = Icons.DOCUMENT_SAVE_AS
    REQUIRES_ACTION = True
    
    lastfolder = get_home_dir()
    
    @classmethod
    def PluginPreferences(self, parent):
        vbox = Gtk.VBox(spacing=6)
        
        queries = {}
        
        query_path = os.path.join(get_user_dir(), 'lists', 'queries.saved')
        with open(query_path, 'rU', encoding='utf-8') as query_file:
            for query_string in query_file:
                name = next(query_file).strip()
                queries[name] = Query(query_string.strip())

        for query_name, query in queries.items():
            check_button = ConfigCheckButton((query_name), "plugins", self._config_key(query_name))
            check_button.set_active(self.config_get_bool(query_name))
            vbox.pack_start(check_button, False, True, 0)
        
        chooserButton = Gtk.FileChooserButton(_('Select destination folder'))
        chooserButton.set_current_folder(self.lastfolder)
        chooserButton.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        
        # https://stackoverflow.com/a/14742779/109813
        def get_actual_filename(name):
            # Do nothing except on Windows
            if os.name != 'nt':
                return name
                
            dirs = name.split('\\')
            # disk letter
            test_name = [dirs[0].upper()]
            for d in dirs[1:]:
                test_name += ["%s[%s]" % (d[:-1], d[-1])]
            res = glob.glob('\\'.join(test_name))
            if not res:
                # File not found, return the input
                return name
            return res[0]
        
        def __file_error(file_path):
            qltk.ErrorMessage(
                None,
                _("Unable to export playlist"),
                _("Writing to <b>%s</b> failed.") % util.escape(file_path)).run()
        
        def __m3u_export(dir_path, query_name, songs):
            file_path = os.path.join(dir_path, query_name + '.m3u')
            try:
                fhandler = open(file_path, "wb")
            except IOError:
                __file_error(file_path)
            else:
                text = "#EXTM3U\n"

                for song in songs:
                    title = "%s - %s" % (
                        song('~people').replace("\n", ", "),
                        song('~title~version'))
                    path = song('~filename')
                    path = get_actual_filename(path)
                    try:
                        path = relpath(path, dir_path)
                    except ValueError:
                        # Keep absolute path
                        pass
                    text += "#EXTINF:%d,%s\n" % (song('~#length'), title)
                    text += path + "\n"

                fhandler.write(text.encode("utf-8"))
                fhandler.close()
        

        def __start(button):
            target_folder = chooserButton.get_filename()

            songs = app.library.get_content();
            for query_name, query in queries.items():
                if self.config_get_bool(query_name):
                    # Query is enabled
                    songs_for_query = query.filter(songs)
                    __m3u_export(target_folder, query_name, songs_for_query)
                    
            message = qltk.Message(Gtk.MessageType.INFO, app.window, _("Done"), _("Export finished."))
            message.run()

        start_button = Gtk.Button(label=("Export"))
        start_button.connect('clicked', __start)

        vbox.pack_start(chooserButton, True, True, 0)
        vbox.pack_start(start_button, True, True, 0)
        label = Gtk.Label(label="Quod Libet may become unresponsive. You will get a message when finished.")
        vbox.pack_start(label, True, True, 0)
        return qltk.Frame(("Select the saved searches to copy:"), child=vbox)
