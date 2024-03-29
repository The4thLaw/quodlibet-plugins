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

import threading
import os
import re
from os.path import relpath
from pathlib import Path
from gi.repository import GLib, Gtk
from quodlibet import _, app, get_user_dir, qltk
from quodlibet.plugins import PluginConfigMixin
from quodlibet.plugins.events import EventPlugin
from quodlibet.qltk import Icons
from quodlibet.qltk.ccb import ConfigCheckButton
from quodlibet.query import Query
from quodlibet.util.dprint import print_d
from quodlibet.util.path import get_home_dir

class ExportSavedSearches(EventPlugin, PluginConfigMixin):
    PLUGIN_ID = 'ExportSavedSearches'
    PLUGIN_NAME = _('Export saved searches')
    PLUGIN_DESC = _('Exports saved searches to M3U playlists.')
    PLUGIN_ICON = Icons.DOCUMENT_SAVE_AS
    REQUIRES_ACTION = True
    
    lastfolder = get_home_dir()

    def showSuccess():
        successMessage = qltk.Message(Gtk.MessageType.INFO, app.window, _("Done"), _("Export finished."))
        successMessage.run()

    # https://stackoverflow.com/a/39140604/109813
    def casedpath_unc(path):
        unc, p = os.path.splitdrive(path)
        r = glob.glob(unc + re.sub(r'([^:/\\])(?=[/\\]|$)|\[', r'[\g<0>]', p))
        return r and r[0] or path

    def get_actual_filename2(path):
        orig_path = path
        path = os.path.normpath(path)

        # Build root to start searching from.  Different for unc paths.
        if path.startswith(r'\\'):
            path = path.lstrip(r'\\')
            path_split = path.split('\\')
            # listdir doesn't work on just the machine name
            if len(path_split) < 3:
                return orig_path
            test_path = r'\\{}\{}'.format(path_split[0], path_split[1])
            start = 2
        else:
            path_split = path.split('\\')
            test_path = path_split[0] + '\\'
            start = 1

        for i in range(start, len(path_split)):
            part = path_split[i]
            if os.path.isdir(test_path):
                for name in os.listdir(test_path):
                    if name.lower() == part.lower():
                        part = name
                        break
                test_path = os.path.join(test_path, part)
            else:
                return orig_path
        return test_path

    # https://stackoverflow.com/a/54984701/109813
    def get_actual_filename(name):
        # Do nothing except on Windows
        if os.name != 'nt':
            return name
        
        print_d('QuodLibet-known name is', name)
        # Old solution, does not cope with case sensitivity
        # actual = str(Path(name).resolve())
        # Super slow, copes with case sensitivity
        # actual = casedpath_unc(name)
        # Also slow, though a bit faster, copes with case sensitivity
        actual = get_actual_filename2(name)
        # One day try this: https://stackoverflow.com/a/3694799
        print_d('Actual file name is', actual)
        return actual
    
    def __file_error(file_path):
        qltk.ErrorMessage(
            None,
            _("Unable to export playlist"),
            _("Writing to <b>%s</b> failed.") % util.escape(file_path)).run()
        
    def export_all(self, target_folder, queries):
        songs = app.library.get_content()

        self.mainProgressBar.set_fraction(0)

        totalQueries = 0
        for query_name, query in queries.items():
            if self.config_get_bool(query_name):
                # Query is enabled
                totalQueries += 1

        currentQuery = 0
        self.mainProgressBar.set_show_text(True)
        self.mainProgressBar.set_text(str(currentQuery) + ' / ' + str(totalQueries))
        for query_name, query in queries.items():
            if self.config_get_bool(query_name):
                # Query is enabled
                songs_for_query = query.filter(songs)
                self.m3u_export(self, target_folder, query_name, songs_for_query)
                currentQuery += 1
                self.mainProgressBar.set_fraction(currentQuery / totalQueries)
                self.mainProgressBar.set_text(str(currentQuery) + ' / ' + str(totalQueries))

        self.progressDialog.destroy()

        # Show dialog on GUI thread
        GLib.timeout_add(0, self.showSuccess)        
        
    def m3u_export(self, dir_path, query_name, songs):
        print_d('Processing playlist', query_name)
        self.progressLabel.set_text('Processing playlist ' + query_name)
        file_path = os.path.join(dir_path, query_name + '.m3u')
        try:
            fhandler = open(file_path, "wb")
        except IOError:
            self.__file_error(file_path)
        else:
            text = "#EXTM3U\n"

            curSong = 0
            totalSongs = len(songs)
            self.subProgressBar.set_fraction(0)
            self.subProgressBar.set_show_text(True)
            self.subProgressBar.set_text(str(curSong) + ' / ' + str(totalSongs))
            for song in songs:
                title = "%s - %s" % (
                    song('~people').replace("\n", ", "),
                    song('~title~version'))
                path = song('~filename')
                path = self.get_actual_filename(path)
                try:
                    path = relpath(path, dir_path)
                except ValueError:
                    # Keep absolute path
                    pass
                text += "#EXTINF:%d,%s\n" % (song('~#length'), title)
                text += path + "\n"
                curSong += 1
                self.subProgressBar.set_fraction(curSong / totalSongs)
                self.subProgressBar.set_text(str(curSong) + ' / ' + str(totalSongs))

            fhandler.write(text.encode("utf-8"))
            fhandler.close()
            self.subProgressBar.set_fraction(0)
    
    @classmethod
    def PluginPreferences(self, parent):
        mainBox = Gtk.VBox(spacing=6)

        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)

        listVbox = Gtk.VBox(spacing=6)
        mainBox.pack_start(listVbox, True, True, 0)
        swin = Gtk.ScrolledWindow()
        swin.set_hexpand(True)
        swin.set_vexpand(True)
        swin.add(listbox)
        listVbox.pack_start(swin, True, True, 0)
        
        queries = {}
        
        query_path = os.path.join(get_user_dir(), 'lists', 'queries.saved')
        with open(query_path, 'r', encoding='utf-8', newline=None) as query_file:
            for query_string in query_file:
                name = next(query_file).strip()
                queries[name] = Query(query_string.strip())

        for query_name, query in queries.items():
            check_button = ConfigCheckButton((query_name), "plugins", self._config_key(query_name))
            check_button.set_active(self.config_get_bool(query_name))
            row = Gtk.ListBoxRow()
            row.add(check_button)
            listbox.add(row)
        
        chooserButton = Gtk.FileChooserButton(_('Select destination folder'))
        chooserButton.set_current_folder(self.lastfolder)
        chooserButton.set_action(Gtk.FileChooserAction.SELECT_FOLDER)

        self.progressDialog = Gtk.Dialog(title=_('Progress'),
                         parent=app.window,
                         flags=(Gtk.DialogFlags.MODAL |
                                Gtk.DialogFlags.DESTROY_WITH_PARENT))
        self.progressDialog.vbox.set_spacing(5)
        self.progressLabel = Gtk.Label()
        self.progressDialog.vbox.add(self.progressLabel)
        self.mainProgressBar = Gtk.ProgressBar()
        self.progressDialog.vbox.add(self.mainProgressBar)
        self.subProgressBar = Gtk.ProgressBar()
        self.progressDialog.vbox.add(self.subProgressBar)

        def __start(_):
            target_folder = chooserButton.get_filename()
            self.progressDialog.show_all()

             # Work in a thread to avoid locking up the UI
            thread = threading.Thread(target=self.export_all,
                                            args=(self, target_folder, queries))
            thread.start()

        startButton = Gtk.Button(label=("Export"))
        startButton.connect('clicked', __start)

        mainBox.pack_start(chooserButton, False, False, 0)
        mainBox.pack_start(startButton, False, False, 0)
        label = Gtk.Label(label="Quod Libet may become unresponsive. You will get a message when finished.")
        mainBox.pack_start(label, False, False, 0)
        return qltk.Frame(("Select the saved searches to copy:"), child=mainBox)
