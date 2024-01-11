# quodlibet-plugins

Custom [Quod Libet](https://github.com/quodlibet/quodlibet) plugins.

## Compatibility

The plugins have been tested using Quod Libet 4.1, 4.4, 4.5, 4.6.

## Plugins

### exportsavedsearches

This plugin allows exporting saved searches as M3U playlist in batches.

Beware that due to the lack of an efficient way of getting the case-sensitive name of a file on Windows, performance on that OS is abysmal (a thousand times slower or more).

### playlistsizetruncaterandom

This plugin truncates a playlist to a size in MB by removing random songs.

**Warning:** The original playlist is modified by this process. Make a copy if it's important.

### playlistsize

Obsolete, Quod Libet now features this out of the box.
