import functools

from .router import router
from .apis import tmdb
from .apis import trakt
from .apis import tvdb


trakt.get = functools.partial(trakt.get,
                              auth_token=router.addon.getSettingString(
                                  'trakt.access_token'))


TRAKT_TRANSLATION = (('title', 'title'),
                     ('year', 'year'),
                     ('overview', 'plot'),
                     ('released', 'premiered'),
                     ('certification', 'mpaa'),
                     ('genres', 'genres'),
                     (('ids', 'imdb'), 'imdbnumber'),
                     ('network', 'studio'),)


TVDB_EPISODE_TRANSLATION = (('episodeName', 'title'),
                            ('imdbId', 'imdbnumber'),
                            ('overview', 'plot'),
                            ('firstAired', 'aired'),)


def translate_info(translation, data):
    info_label = {}
    for data_key, info_label_key in translation:
        try:
            basestring
        except NameError:
            basestring = str
        if isinstance(data_key, basestring):
            value = data.get(data_key)
        else:
            value = data
            for subkey in data_key:
                value = value.get(subkey, {})
        if value:
            info_label[info_label_key] = value
    return info_label


def trakt_movie(imdbid):
    path = 'movies/{}'.format(imdbid)
    result = trakt.get(path, extended='full')
    return result


def trakt_movies_popular(page=1):
    path = 'movies/popular'
    result = trakt.get(path, extended='full', page=page)
    return result


def trakt_show(imdbid):
    path = 'shows/{}'.format(imdbid)
    result = trakt.get(path, extended='full')
    return result


def trakt_seasons(imdbid, extended=False):
    path = 'shows/{}/seasons'.format(imdbid)
    if extended:
        result = trakt.get(path, extended='full,episodes')
    else:
        result = trakt.get(path)
    return result


def trakt_season(imdbid, season, extended=False):
    path = 'shows/{}/seasons/{:d}'.format(imdbid, int(season))
    if extended:
        result = trakt.get(path, extended='full')
    else:
        result = trakt.get(path)
    return result


def trakt_episode(imdbid, season, episode):
    path = 'shows/{}/seasons/{:d}/episodes/{:d}'.format(imdbid,
                                                        int(season),
                                                        int(episode))
    result = trakt.get(path, extended='full')
    return result


def trakt_liked_lists(page=1):
    path = '/users/likes/lists'
    result = trakt.get(path, page=page)
    return result


def trakt_list(user, list_id, _type):
    path = '/users/{}/lists/{}/items/{}'.format(user, list_id, _type)
    result = trakt.get(path, extended='full')
    return result


@tvdb.jwt_auth
def tvdb_show(jwt, tvdb_seriesid):
    path = 'series/{}'.format(tvdb_seriesid)
    result = tvdb.get(jwt, path)['data']
    path = 'series/{}/episodes/summary'.format(tvdb_seriesid)
    result.update(tvdb.get(jwt, path)['data'])
    return result


@tvdb.jwt_auth
def tvdb_show_images(jwt, tvdb_seriesid, keyType='fanart'):
    path = 'series/{}/images/query'.format(tvdb_seriesid)
    result = tvdb.get(jwt, path, keyType=keyType)
    return result


@tvdb.jwt_auth
def tvdb_season(jwt, tvdb_seriesid, season):
    path = 'series/{}/episodes/query'.format(tvdb_seriesid)
    result = tvdb.get(jwt, path, airedSeason=season)['data']
    return result


@tvdb.jwt_auth
def tvdb_episode(jwt, tvdb_episodeid):
    path = 'episodes/{}'.format(tvdb_episodeid)
    result = tvdb.get(jwt, path)
    return result


@router.memcache
def tmdb_movie(tmdb_id):
    return tmdb.get('/movie/{}'.format(tmdb_id))
