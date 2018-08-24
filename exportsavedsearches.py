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

import os
from os.path import relpath
from gi.repository import Gtk
from quodlibet import _, app
from quodlibet import get_user_dir
from quodlibet import qltk
from quodlibet.plugins.events import EventPlugin
from quodlibet.plugins.songsmenu import SongsMenuPlugin
from quodlibet.qltk.ccb import ConfigCheckButton
from quodlibet.query import Query
from quodlibet.plugins import PluginConfigMixin
from quodlibet import config
from quodlibet.qltk import Icons
from quodlibet.plugins.songshelpers import any_song, is_finite
from quodlibet.library import SongLibrary
from pprint import pprint
from quodlibet.util.path import glib2fsn, get_home_dir


class ExportSavedSearches(EventPlugin, PluginConfigMixin):
    PLUGIN_ID = 'ExportSavedSearches'
    PLUGIN_NAME = _('Export saved searches')
    PLUGIN_DESC = _('Exports saved searches to M3U or PLS playlists.')
    PLUGIN_ICON = Icons.DOCUMENT_SAVE_AS
    REQUIRES_ACTION = True
    
    #plugin_handles = any_song(is_finite)
    lastfolder = get_home_dir()
    
    @classmethod
    def PluginPreferences(self, parent):
        vbox = Gtk.VBox(spacing=6)
        
        #print(app.library.get_content())

        queries = {}
        query_path = os.path.join(get_user_dir(), 'lists', 'queries.saved')
        with open(query_path, 'rU') as query_file:
            for query_string in query_file:
                name = next(query_file).strip()
                queries[name] = Query(query_string.strip())

        for query_name, query in queries.items():
            check_button = ConfigCheckButton((query_name), "plugins", self._config_key(query_name))
            check_button.set_active(self.config_get_bool(query_name))
            vbox.pack_start(check_button, False, True, 0)
            
        def __select_folder():
            folderDialog = Gtk.FileChooserDialog(self.PLUGIN_NAME,
                self,
                Gtk.FileChooserAction.SELECT_FOLDER)
            folderDialog.set_show_hidden(False)
            folderDialog.set_create_folders(True)
            folderDialog.add_button(_("_Cancel"), Gtk.ResponseType.CANCEL)
            folderDialog.add_button(_("_Save"), Gtk.ResponseType.OK)
            folderDialog.set_default_response(Gtk.ResponseType.OK)
        
        chooserButton = Gtk.FileChooserButton("a")
        chooserButton.set_current_folder(self.lastfolder)
        chooserButton.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        
        def __file_error(file_path):
            qltk.ErrorMessage(
                None,
                _("Unable to export playlist"),
                _("Writing to <b>%s</b> failed.") % util.escape(file_path)).run()

        
        def __m3u_export(dir_path, query_name, songs):
            file_path = os.path.join(dir_path, query_name + '.m3u')
            print (file_path)
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
                    path = relpath(path, dir_path)
                    text += "#EXTINF:%d,%s\n" % (song('~#length'), title)
                    text += path + "\n"

                fhandler.write(text.encode("utf-8"))
                fhandler.close()
        

        def __start(button):
            #enabled_queries = []
            #for query_name, query in queries.items():
            #    if self.config_get_bool(query_name):
            #        enabled_queries.append(query)
            #print(enabled_queries)
            target_folder = chooserButton.get_filename()

            songs = app.library.get_content();
            for query_name, query in queries.items():
                if self.config_get_bool(query_name):
                    # Query is enabled
                    print('Processing query: ' + query_name)
                    songs_for_query = query.filter(songs)
                    __m3u_export(target_folder, query_name, songs_for_query)
                    
            
            message = qltk.Message(Gtk.MessageType.INFO, app.window, _("Done"), _("Export finished."))
            message.run()


        start_button = Gtk.Button(label=("Export"))
        start_button.connect('clicked', __start)

        #vbox.pack_start(destination_path_box, True, True, 0)
        vbox.pack_start(chooserButton, True, True, 0)
        vbox.pack_start(start_button, True, True, 0)
        label = Gtk.Label(label="Quod Libet may become unresponsive. You will get a message when finished.")
        vbox.pack_start(label, True, True, 0)
        return qltk.Frame(("Select the saved searches to copy:"), child=vbox)