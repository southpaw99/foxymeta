import functools
import time
import urllib

import xbmc
import xbmcgui
import xbmcplugin

from resources.lib import metadata
from resources.lib.apis import tmdb, trakt
from resources.lib.router import router



def ui_trakt_list_movies(func, period=False):
    def wrapper(page=1):
        if period:
            _list = '{}/{}'.format(func.__name__,
                                   router.addon.getSettingString(
                                       'list.time.period').lower())
        else:
            _list = func.__name__
        for movie in metadata.trakt_movies(_list=_list, page=page):
            li = metadata.movie_listitem(trakt_data=movie)
            li.setProperty('IsPlayable', 'true')
            xbmcplugin.addDirectoryItem(router.handle,
                                        foxy_movie_uri(movie['ids']['imdb']),
                                        li, False)
        xbmcplugin.addDirectoryItem(router.handle,
                                    router.build_url(globals()[func.__name__],
                                                     page=int(page)+1),
                                    xbmcgui.ListItem('Next'),
                                    True)
        xbmcplugin.endOfDirectory(router.handle)
    return wrapper


ui_trakt_list_movies_period = functools.partial(ui_trakt_list_movies,
                                                period=True)


@router.route('/trakt/popular')
@ui_trakt_list_movies
def popular(page=1):
    pass


@router.route('/trakt/played')
@ui_trakt_list_movies_period
def played(page=1):
    pass


@router.route('/trakt/trending')
@ui_trakt_list_movies
def trending(page=1):
    pass


@router.route('/trakt/watched')
@ui_trakt_list_movies_period
def watched(page=1):
    pass


@router.route('/trakt/collected')
@ui_trakt_list_movies_period
def collected(page=1):
    pass


@router.route('/trakt/anticipated')
@ui_trakt_list_movies
def anticipated(page=1):
    pass


@router.route('/trakt/boxoffice')
@ui_trakt_list_movies
def boxoffice(page=1):
    pass


@router.route('/trakt/updates')
def updates(page=1):
    start_date = time.strftime('%Y-%m-%d', time.gmtime())
    _list = 'updates/{}'.format(start_date)
    for movie in metadata.trakt_movies(_list=_list, page=page):
        li = metadata.movie_listitem(trakt_data=movie)
        xbmcplugin.addDirectoryItem(router.handle,
                                    foxy_movie_uri(movie['ids']['imdb']),
                                    li, False)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(updates, page=int(page)+1),
                                xbmcgui.ListItem('Next'),
                                True)
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/trakt/liked_lists')
def liked_lists(page=1):
    for _list in metadata.trakt_liked_lists(page=page):
        li = xbmcgui.ListItem(_list['list']['name'])
        url = router.build_url(trakt_list,
                               user=_list['list']['user']['ids']['slug'],
                               list_id=_list['list']['ids']['trakt'])
        xbmcplugin.addDirectoryItem(router.handle,
                                    url,
                                    li, True)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(liked_lists, page=int(page)+1),
                                xbmcgui.ListItem('Next'),
                                True)
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/trakt/list')
def trakt_list(user, list_id):
    for item in metadata.trakt_list(user, list_id, 'movies'):
        movie = item['movie']
        li = metadata.movie_listitem(trakt_data=movie)
        li.setInfo('video', {
            'dateadded': ' '.join(item['listed_at'].split('.')[0].split('T')),
        })
        li.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(router.handle,
                                    foxy_movie_uri(movie['ids']['imdb']),
                                    li, False)
    xbmcplugin.addSortMethod(router.handle, xbmcplugin.SORT_METHOD_DATEADDED)
    xbmcplugin.endOfDirectory(router.handle)



@router.route('/tmdb/trending')
def tmdb_trending(media_type='movie', page=1):
    result = metadata.tmdb_trending(media_type='movie', page=page)
    for item in result['results']:
        li = metadata.movie_listitem(tmdb_data=item)
        li.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(router.handle,
                                    foxy_movie_uri(item['id'], src='tmdb'),
                                    li, False)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(tmdb_trending,
                                                 page=int(page)+1),
                                xbmcgui.ListItem('Next'),
                                True)
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/app/movies')
def movies():
    def diritem(func, name):
        xbmcplugin.addDirectoryItem(router.handle,
                                    router.build_url(func),
                                    xbmcgui.ListItem(name),
                                    True)
    diritem(popular, 'Popular Movies')
    diritem(trending, 'Trending Movies')
    diritem(tmdb_trending, 'Trending Movies (TMDB)')
    diritem(played, 'Most Played Movies')
    diritem(watched, 'Most Watched Movies')
    diritem(collected, 'Most Collected Movies')
    diritem(anticipated, 'Most Anticipated Movies')
    diritem(boxoffice, 'Box Office Top 10')
    diritem(updates, 'Recently Updated Movies')
    diritem(liked_lists, 'Liked Lists')
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/')
def root():
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(movies),
                                xbmcgui.ListItem('Movies'),
                                True)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(authenticate_trakt),
                                xbmcgui.ListItem('Auth Trakt'),
                                False)
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/auth_trakt')
def authenticate_trakt():
    init = trakt.authenticate()
    dialog = xbmcgui.DialogProgress()
    dialog.create('Enter code at: {}'.format(init['verification_url']),
                  init['user_code'])
    expires = time.time() + init['expires_in']
    while True:
        time.sleep(init['interval'])
        try:
            token = trakt.authenticate(init['device_code'])
        except Exception:
            pct_timeout = (time.time() - expires) / init['expires_in'] * 100
            pct_timeout = 100 - int(abs(pct_timeout))
            if pct_timeout >= 100 or dialog.iscanceled():
                dialog.close()
                xbmcgui.Dialog().notification('FoxyMeta', 'Trakt Auth failed')
                return
            dialog.update(int(pct_timeout))
        else:
            dialog.close()
            save_trakt_auth(token)
            return


def save_trakt_auth(response):
    router.addon.setSettingString('trakt.access_token',
                                  response['access_token'])
    router.addon.setSettingString('trakt.refresh_token',
                                  response['refresh_token'])
    expires = response['created_at'] + response['expires_in']
    router.addon.setSettingInt('trakt.expires', expires)


def foxy_movie_uri(_id, src='imdb'):
    base_uri = 'plugin://plugin.video.foxystreams/play/movie?'
    if src == 'tmdb':
        _id = tmdb.get('/movie/{}/external_ids'.format(_id))['imdb_id']
    return base_uri + urllib.urlencode({'imdb': _id})


if __name__ == '__main__':
    xbmcplugin.setContent(router.handle, 'movies')
    router.run()