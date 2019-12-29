from . import metadata
from .router import router

import xbmcgui
import xbmcplugin



@router.route('/tv/trakt/popular')
def tv_popular(page=1):
    for show in metadata.trakt_shows(page=page):
        li = metadata.show_listitem(trakt_data=show)
        xbmcplugin.addDirectoryItem(router.handle,
                                    router.build_url(
                                        tv_show,
                                        tvdbid=show['ids']['tvdb']),
                                    li,
                                    True)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(tv_popular,
                                                 page=int(page)+1),
                                xbmcgui.ListItem('Next'),
                                True)
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/tv/tvdb/show')
def tv_show(tvdbid=None):
    for season in metadata.tvdb_show(tvdbid)['airedSeasons']:
        li = xbmcgui.ListItem(season)
        xbmcplugin.addDirectoryItem(router.handle,
                                    router.build_url(
                                        tv_season,
                                        tvdbid=tvdbid,
                                        season=season),
                                    li,
                                    True)
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/tv/tvdb/season')
def tv_season(tvdbid=None, season=None):
    for episode in metadata.tvdb_season(tvdbid, season):
        li = metadata.episode_listitem(tvdb_data=episode)
        xbmcplugin.addDirectoryItem(router.handle,
                                    '',
                                    li,
                                    False)
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/app/tv')
def root():
    router.gui_dirlist([(tv_popular, 'Popular TV')],
                       dirs=True)
