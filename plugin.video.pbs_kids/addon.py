# stdlib
from collections import namedtuple
import math
import urllib, sys
import urllib2
from xml.dom.minidom import parseString

# 3p
import simplejson as json

# XMBC libs
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

class PBSRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        raise Exception(headers['location'])

    http_error_301 = http_error_303 = http_error_307 = http_error_302


Show = namedtuple('Show', ['title', 'plot', 'thumbnail'])
Video = namedtuple('Video', ['title', 'plot', 'duration', 'thumbnail', 'url',
                             'type'])

class PBSKids(object):
    # Shows constants
    SHOWS_URL = 'http://pbskids.org/shell/video/data/org.pbskids.shows.json'
    SHOW_THUMB_BASE = "http://www-tc.pbskids.org/shell/images/"\
                      "content/show-bubbles/circle/%s"

    # Videos constants
    PER_PAGE = 25
    VIDEOS_BASE = "http://pbskids.org/pbsk/video/api/getVideos/?"\
                  "startindex={startindex}&endindex={endindex}"\
                  "&program={program}&status=available&player=flash&flash=true"\
                  "&return="

    # Video bitrates sorted by preference.
    BITRATES = [2500, 1200, 800, 400]
    
    def __init__(self):
        pass

    def get_shows(self):
        response = json.loads(urllib.urlopen(self.SHOWS_URL).read())
        return [Show(
            title=show['title'],
            plot=show['description'],
            thumbnail=self.SHOW_THUMB_BASE % show['whiteCircle']
        ) for show in response]


    def get_videos(self, program, page):
        """ Returns a tuple of ([Video, ...], more) where `more` is a boolean
            signaling if there are more videos beyond this page.
        """
        start = (page * self.PER_PAGE) + 1
        end = ((page + 1) * self.PER_PAGE)
        url = self.VIDEOS_BASE.format(
                startindex=start,
                endindex=end,
                program=program)
        response = json.loads(urllib.urlopen(url).read())

        videos = []
        for item in response.get('items', []):
            if 'title' not in item:
                continue
            title = item['title']
            plot = item['description']
            video_type = item['type']
            flv_videos = item['videos']['flash']
            duration = self._get_length_string(flv_videos['length'])

            # Pick the "best" flv video we can get.
            # FIXME: Maybe we could do smart streaming eventually?
            url = None
            for br in self.BITRATES:
                key = 'mp4-%sk' % br
                if key in flv_videos:
                    url = flv_videos[key]['url']
                    break
            # Old-style URL
            if 'url' in flv_videos:
                url = flv_videos['url']

            if not url:
                # Skip any videos matching none of our bit rates.
                print(item)
                continue

            # Pick the "best" thumbnail we can (or None)
            images = item['images']
            if 'originalres_16x9' in images:
                thumbnail = images['originalres_16x9']['url']
            elif 'originalres_4x3' in images:
                thumbnail = images['originalres_4x3']['url']
            elif 'googlethumbnail' in images:
                thumbnail = images['googlethumbnail']['url']
            else:
                thumbnail = None

            videos.append(Video(
                title=title,
                plot=plot,
                duration=duration,
                thumbnail=thumbnail,
                url=url,
                type=video_type
            ))

        # Decide if there are more episodes to paginate through.
        more = end < response['matched']

        return videos, more

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
            # some refs are a redirect to the correct video url and
            # some refs return xml info about correct video url
            response = urllib2.urlopen(start_url)
            # only reach this point if no redirect
            data = response.read()
            response.close()
            dom = parseString(data)
            xmlnode = dom.getElementsByTagName('url')[0]
            return xmlnode.firstChild.nodeValue.replace('<break>', '')
        except Exception, e:
            # This is an odd way of doing this...
            return str(e).replace('<break>', '')
        
    def get_per_page(self):
        return self.PER_PAGE 

    def _get_length_string(self, lenval):
        minpart = int(math.floor(lenval / 60000))
        secpart = str(int(((lenval - (minpart * 60000)) / 1000)))
        if len(secpart) == 1:
            secpart = '0' + secpart
        return str(minpart) + ':' + secpart


__addon__ = xbmcaddon.Addon(id='plugin.video.pbs_kids')
__info__ = __addon__.getAddonInfo
__plugin__ = __info__('name')
__version__ = __info__('version')
__icon__ = __info__('icon')
__fanart__ = __info__('fanart')

PLUGIN = sys.argv[0]
HANDLE = int(sys.argv[1])
PARAMS = sys.argv[2]

class Main(object):
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
        for show in shows:
            item = xbmcgui.ListItem(label=show.title,
                                    thumbnailImage=show.thumbnail)
            url = '%s?action=vids&show=%s' % (PLUGIN, urllib.quote(show.title))
            xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=item,
                                        isFolder=True, totalItems=len(shows))
        # Sort by show name (is this necessary?)
        xbmcplugin.addSortMethod(handle=HANDLE,
            sortMethod=xbmcplugin.SORT_METHOD_TITLE)

        # End the directory
        xbmcplugin.endOfDirectory(handle=HANDLE, succeeded=True)

    def videos_menu(self):
        params = self._get_params_dict()
        show = params['show']
        try:
            page = int(params['page'])
        except:
            page = 0

        videos, more = self.pbs.get_videos(show, page)
        for video in videos:
            label = video.title
            if video.type == 'Episode':
                label += ' (Full Episode)'
            elif video.type == 'Clip':
                label += ' (Clip)'

            # Add episode items to menu
            item = xbmcgui.ListItem(
                label=label,
                iconImage='DefaultFolder.png',
                thumbnailImage=video.thumbnail or ''
            )
            item.setInfo('video', {
                'plot': video.plot,
                'duration': video.duration
            })

            # Set directory URL for xbmc
            params = {
                'action': 'play',
                'vid_url': urllib.quote(video.url),
                'show': urllib.quote(show),
                'title': urllib.quote(video.title.encode('utf-8','ignore'))
            }
            xbmcplugin.addDirectoryItem(
                handle=HANDLE,
                url='%s%s' % (PLUGIN, self._params_to_string(params)),
                listitem=item,
                isFolder=False,
                totalItems=len(video)
            )

        # Add 'more' button if needed
        if more:
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

        xbmc.Player(xbmc.PLAYER_CORE_MPLAYER).play(real_url, listitem)

    def _get_params_dict(self):
        return dict([part.split('=') for part in PARAMS[1:].split('&')])

    def _params_to_string(self, params):
        return '?%s' % ('&'.join(['%s=%s' % (k,v) for k,v in params.items()]))


if __name__ == "__main__":
    pbs = PBSKids()
    Main(pbs)