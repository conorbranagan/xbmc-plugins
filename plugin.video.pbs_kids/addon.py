import urllib, re, sys
import urllib2
from os.path import basename
import simplejson as json

# XMBC libs
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

class PBSRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        raise Exception(headers['location'])

    http_error_301 = http_error_303 = http_error_307 = http_error_302

class PBSKids(object):
    shows = [
        ('Angelina Ballerina', 'http://t1.gstatic.com/images?q=tbn:ANd9GcRauKYR1woxi25U7nrir2AN-YAwFrWcz5nsx-MaAS_aCw05xX5BCA'),
        ('Arthur', 'http://t2.gstatic.com/images?q=tbn:ANd9GcQJvPZKKJRWBRLhkyZJ7sXKV-jHUv9XkieAIQl_9p38ca-bSvoA'),
        ('Between the Lions', 'http://t1.gstatic.com/images?q=tbn:ANd9GcQ_wUeItEx09KPu_cHUfsQZc_X-XRGEEmksf-WG_GZ2BPAJSe-g9Q'),
        ('Clifford the Big Red Dog', 'http://t1.gstatic.com/images?q=tbn:ANd9GcTdLVRdpxTD666-q4wEWIQj8DXGXOHInHKt-S2S8mZ8jE6nrp9l'),
        ('Curious George', 'http://t1.gstatic.com/images?q=tbn:ANd9GcQkW4nd6_VCrFNO712FFWWLBNRsAGMsNi1ye39N6SSm87mzYXD2SA'),
        ('Dinosaur Train', 'http://t1.gstatic.com/images?q=tbn:ANd9GcSSy-zPxW3kv492RzBHkyoDKnbj_m2t6AAI8QtTMNULe8i5XMzt'),
        ('Hooper', 'http://t3.gstatic.com/images?q=tbn:ANd9GcSBMEB-a-xkVxJPxB6YtJSf3B3gFj_tr0ws-Tm4hXpyLctwzUO6LA'),
        ('Lomax the Hound of Music', 'http://t0.gstatic.com/images?q=tbn:ANd9GcRWoED5Z9Ole3ZQuGlNrhFHzVyDb-B-lauATmnq95B2j56HiS3g'),
        ('Mama Mirabelle\'s Home Movies', 'http://t3.gstatic.com/images?q=tbn:ANd9GcT4VIlhiiqnBbMWsIRuH8LVPddPqes99o6-sghPXtmHnIhwTJUCIQ'),
        ('Martha Speaks', 'http://t1.gstatic.com/images?q=tbn:ANd9GcSwrQm2lCbnV606Nbt7xXzBBr9HMBjOnfUbFhhzUFDcwS1or_KvlA'),
        ('Mister Rogers\' Neighborhood', 'http://t2.gstatic.com/images?q=tbn:ANd9GcTA0VaXsO3CPZe5oOk3arBF2LGy-tkMJA-KUBvMYE62xzhT1xOT'),
        ('Music Time with SteveSongs', 'http://t3.gstatic.com/images?q=tbn:ANd9GcQwVtrBXy-dd4WNFQ-7ecT1oCFZtGnB4wLBKa0sm3BBERwjGaW8Rw'),
        ('Sesame Street', 'http://t1.gstatic.com/images?q=tbn:ANd9GcRpZ01x49DLroVefKunsZq-BQndEsmqIZ2uF5NpsH7x1Qppza-n'),
        ('Sid The Science Kid', 'http://t3.gstatic.com/images?q=tbn:ANd9GcToL4xx-kAaBf0az48kA2MAWVvgBoNQJfpBWtN4Kt8J_xfhx95LFQ'),
        ('Super Why', 'http://t3.gstatic.com/images?q=tbn:ANd9GcTPbtuOPgQey4mshrFZifIP3FS1yq4_bqlcKC6AzFsrgN_K5y5Gsw'),
        ('The Cat in the Hat', 'http://t2.gstatic.com/images?q=tbn:ANd9GcRbQob8R63vpLxmj9-SZ2jMSeDAVcgDOZLwIzKuGmhxcLIvWn3w'),
        ('WordWorld', 'http://t2.gstatic.com/images?q=tbn:ANd9GcQzAKKTUrU3HsStbgMQ7tGCJQjlCW9-kUbjQOmuiQbZr6qH9bKsUQ'),
    ]

    PER_PAGE = 10
    VIDEOS_BASE = 'http://pbs.feeds.theplatform.com/ps/JSON/PortalService/2.2/getReleaseList?PID=6HSLquMebdOkNaEygDWyPOIbkPAnQ0_C&startIndex=%s&endIndex=%s&query=Categories|%s&sortField=airdate&sortDescending=true&field=title&field=categories&field=airdate&field=expirationDate&field=length&field=description&field=language&field=thumbnailURL&field=URL&field=PID&contentCustomField=IsClip'

    def __init__(self):
        pass

    def get_shows(self):
        return self.shows

    def get_episodes(self, show, page):
        start = (page * self.PER_PAGE) + 1
        end = ((page + 1) * self.PER_PAGE)
        url = self.VIDEOS_BASE % (start, end, urllib.quote(show))
        videos = json.loads(urllib.urlopen(url).read())

        eps = []
        for i in videos['items']:
            eps.append(i)
        return eps, videos['listInfo']['totalCount']

    def _get_ext(self, show):
        if show in self.all_flv:
            return "flv"
        return "mp4"

    def get_video_url(self, start_url):
        # This may have to be adjusted if PBS changes
        # either the base cloudfront.net url or anything
        # else, but for now, we are just doing a conversion
        # based on how it's looking right now
        opener = urllib2.build_opener(PBSRedirectHandler)
        urllib2.install_opener(opener)

        try:
            response = urllib2.urlopen(start_url)
        except Exception, e:
            return str(e).replace('<break>', '') # This is an odd way of doing this...

__addon__ = xbmcaddon.Addon(id='plugin.video.pbs_kids')
__info__ = __addon__.getAddonInfo
__plugin__ = __info__('name')
__version__ = __info__('version')
__icon__ = __info__('icon')
__fanart__ = __info__('fanart')

PLUGIN = sys.argv[0]
HANDLE = int(sys.argv[1])
PARAMS = sys.argv[2]

class Main:
    def __init__(self, pbs):
        self.pbs = pbs

        if 'action=vids' in PARAMS:
            self.videos_menu()
        elif 'action=play' in PARAMS:
            self.play_vid()
        else:
            self.shows_menu()

    def shows_menu(self):
        """ Main show menu
        """
        shows = pbs.get_shows()
        for show, thumbnail in shows:
            item = xbmcgui.ListItem(label=show, thumbnailImage=thumbnail)
            url = '%s?action=vids&show=%s' % (PLUGIN, show)
            xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=item, isFolder=True, totalItems=len(shows))
        # Sort by show name (is this necessary?)
        xbmcplugin.addSortMethod(handle=HANDLE, sortMethod=xbmcplugin.SORT_METHOD_TITLE)

        # End the directory
        xbmcplugin.endOfDirectory(handle=HANDLE, succeeded=True)

    def videos_menu(self):
        params = self._get_params_dict()
        show = params['show']
        try:
            page = int(params['page'])
        except:
            page = 0

        episodes, total = self.pbs.get_episodes(show, page)
        for ep in episodes:
            label = ep['title']
            if ep['contentCustomData'][0]['value'] == 'false':
                label += ' (Full Episode)'

            item = xbmcgui.ListItem(
                label=label,
                iconImage='DefaultFolder.png',
                thumbnailImage=ep['thumbnailURL']
            )
            item.setInfo('video', {'plot': ep['description']})
            url = ep['URL']
            params = {
                'action': 'play',
                'vid_url': urllib.quote(url),
                'show': urllib.quote(show),
                'title': urllib.quote(ep['title']),
            }
            xbmcplugin.addDirectoryItem(
                handle=HANDLE,
                url='%s%s' % (PLUGIN, self._params_to_string(params)),
                listitem=item,
                isFolder=False,
                totalItems=len(episodes)
            )

        # Add 'more' button if needed
        if (page + 1) * len(episodes) < total:
            params = self._get_params_dict()
            params['page'] = page + 1
            item = xbmcgui.ListItem(label='More...')
            xbmcplugin.addDirectoryItem(
                handle=HANDLE,
                url='%s%s' % (PLUGIN, self._params_to_string(params)),
                listitem=item,
                isFolder=True
            )

        # End the directory
        xbmcplugin.endOfDirectory(handle=HANDLE, succeeded=True)

    def play_vid(self):
        params = self._get_params_dict()
        vid_url = urllib.unquote(params['vid_url'])
        show = urllib.unquote(params['show'])
        title = urllib.unquote(params['title'])

        real_url = self.pbs.get_video_url(vid_url)

        # Set video info
        listitem = xbmcgui.ListItem(show)
        listitem.setInfo('video', {'Title': title, 'Genre': 'Kids'})

        xbmc.Player( xbmc.PLAYER_CORE_MPLAYER ).play(real_url, listitem)

    def _get_params_dict(self):
        return dict([part.split('=') for part in PARAMS[1:].split('&')])

    def _params_to_string(self, params):
        return '?%s' % ('&'.join(['%s=%s' % (k,v) for k,v in params.items()]))

if __name__ == "__main__":
    pbs = PBSKids()
    Main(pbs)