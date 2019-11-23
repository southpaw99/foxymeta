import functools

#from .router import router
from . import trakt_api


#trakt_api.get = functools.partial(trakt_api.get,
#                                  auth_token=router.addon.getString(
#                                      'trakt.auth_token'))
trakt_api.get = functools.partial(trakt_api.get,
                                  auth_token='')


def trakt_movie(imdbid):
    path = 'movies/{}'.format(imdbid)
    result = trakt_api.get(path, extended='full')
    return result


def trakt_show(imdbid):
    path = 'shows/{}'.format(imdbid)
    result = trakt_api.get(path, extended='full')
    return result


def trakt_seasons(imdbid, extended=False):
    path = 'shows/{}/seasons'.format(imdbid)
    if extended:
        result = trakt_api.get(path, extended='full,episodes')
    else:
        result = trakt_api.get(path)
    return result

def trakt_season(imdbid, season, extended=False):
    path = 'shows/{}/seasons/{:d}'.format(imdbid, int(season))
    if extended:
        result = trakt_api.get(path, extended='full')
    else:
        result = trakt_api.get(path)
    return result


def trakt_episode(imdbid, season, episode):
    path = 'shows/{}/seasons/{:d}/episodes/{:d}'.format(imdbid,
                                                        int(season),
                                                        int(episode))
    result = trakt_api.get(path, extended='full')
    return result
