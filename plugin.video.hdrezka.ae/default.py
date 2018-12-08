#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, urllib, urllib2, sys
import xbmc, xbmcplugin,xbmcgui,xbmcaddon
import re, json
from operator import itemgetter

import XbmcHelpers
common = XbmcHelpers

import Translit as translit
translit = translit.Translit()

from binascii import unhexlify
from base64 import b64encode
from M2Crypto.EVP import Cipher

try:
    sys.path.append(os.path.dirname(__file__)+ '/../plugin.video.unified.search')
    from unified_search import UnifiedSearch
except:
    pass

QUALITY_TYPES = (360, 480, 720, 1080)

class HdrezkaTV():
    def __init__(self):
        self.id = 'plugin.video.hdrezka.ae'
        self.addon = xbmcaddon.Addon(self.id)
        self.icon = self.addon.getAddonInfo('icon')
        self.fanart = self.addon.getAddonInfo('fanart')
        self.path = self.addon.getAddonInfo('path')
        self.profile = self.addon.getAddonInfo('profile')

        self.language = self.addon.getLocalizedString
        self.inext = os.path.join(self.path, 'resources/icons/next.png')
        self.handle = int(sys.argv[1])
        self.domain = self.addon.getSetting('domain')
        self.url = 'http://' + self.addon.getSetting('domain')
        self.keyfile = os.path.join(self.path, 'keys.dat')

        self.quality = self.addon.getSetting('quality')
        self.deepscan = self.addon.getSetting('deepscan') if self.addon.getSetting('deepscan') else "false"
        self.translator = self.addon.getSetting('translator') if self.addon.getSetting('translator') else "default"
        self.description = self.addon.getSetting('description') if self.addon.getSetting('translator') else "true"

    def main(self):
        params = common.getParameters(sys.argv[2])
        mode = url = page = None

        mode = params['mode'] if 'mode' in params else None
        url = urllib.unquote_plus(params['url']) if 'url' in params else None
        urlm = urllib.unquote_plus(params['urlm']) if 'urlm' in params else None
        page = int(params['page']) if 'page' in params else 1

        post_id = params['post_id'] if 'post_id' in params else None
        season_id = params['season_id'] if 'season_id' in params else None
        episode_id = params['episode_id'] if 'episode_id' in params else None
        title = urllib.unquote_plus(params['title']) if 'title' in params else None
        image = params['image'] if 'image' in params else None

        keyword = params['keyword'] if 'keyword' in params else None
        external = 'unified' if 'unified' in params else None
        if external == None:
            external = 'usearch' if 'usearch' in params else None    

        if mode == 'play':
            self.play(url)
        if mode == 'play_episode':
            self.play_episode(url, urlm, post_id, season_id, episode_id, title, image)
        if mode == 'show':
            self.show(url)
        if mode == 'index':
            self.index(url, page)
        if mode == 'categories':
            self.categories()
        if mode == 'search':
            self.search(keyword, external)
        elif mode == None:
            self.menu()

    def menu(self):
        uri = sys.argv[0] + '?mode=%s&url=%s' % ("search", self.url)
        item = xbmcgui.ListItem("[COLOR=FF00FF00][%s][/COLOR]" % self.language(1000), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=%s&url=%s' % ("categories", self.url)
        item = xbmcgui.ListItem("[COLOR=FF00FFF0]%s[/COLOR]" % self.language(1003), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        self.index(self.url + '/new', 1)

    def categories(self):
        response = common.fetchPage({"link": self.url})
        genres = common.parseDOM(response["content"], "ul", attrs={"id": "topnav-menu"})

        titles = common.parseDOM(genres, "a", attrs={"class": "b-topnav__item-link"})
        links = common.parseDOM(genres, "a", attrs={"class": "b-topnav__item-link"}, ret='href')

        for i, title in enumerate(titles):
            title = common.stripTags(title)
            link = self.url + links[i]

            uri = sys.argv[0] + '?mode=%s&url=%s' % ("index", link)
            item = xbmcgui.ListItem(title, thumbnailImage=self.icon)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def index(self, url, page):
        if(page == 1):
            page_url = url
        else:
            page_url = "%s/page/%s/" % (url, page)

        print page_url

        response = common.fetchPage({"link": page_url})
        content = common.parseDOM(response["content"], "div", attrs={"class": "b-content__inline_items"})
        items = common.parseDOM(content, "div", attrs={"class": "b-content__inline_item"})
        post_ids = common.parseDOM(content, "div", attrs={"class": "b-content__inline_item"}, ret="data-id")

        link_containers = common.parseDOM(items, "div", attrs={"class": "b-content__inline_item-link"})

        links = common.parseDOM(link_containers, "a", ret='href')
        titles = common.parseDOM(link_containers, "a")
        divcovers = common.parseDOM(items, "div", attrs={"class": "b-content__inline_item-cover"})

        country_years = common.parseDOM(link_containers, "div")
        items_count = 0

        usr_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
        headers = {
            "User-Agent": usr_agent,
            "Referer": url
        }

        for i, title in enumerate(titles):
            items_count += 1
            infos = self.get_item_description(url, post_ids[i])

            country_year = country_years[i].split(',')[0].replace('.', '').replace('-', '').replace(' ', '')
            title = "%s [COLOR=55FFFFFF](%s)[/COLOR]" % (title, country_year)
            image = common.parseDOM(divcovers[i], "img", ret='src')[0]

            uri = sys.argv[0] + '?mode=show&url=%s' % links[i]
            item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
            item.setInfo(type='Video', infoLabels={'title': title, 'genre': country_years[i], 'plot': infos['description'], 'rating': infos['rating']})

            if (self.quality != 'select'):
                if self.deepscan == "true":
                    request = urllib2.Request(links[i], "", headers)
                    request.get_method = lambda: 'GET'
                    response = urllib2.urlopen(request).read()
                    src_url_iframe = response.split('<iframe ')[-1].split('>')[0]
                    if (not 'season' in src_url_iframe) or ('season=&' in src_url_iframe):
                        item.setProperty('IsPlayable', 'true')
                        xbmcplugin.addDirectoryItem(self.handle, uri, item, False)
                    else:
                        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
                else:
                    if (not ('/series/' in url)) and (not ('/show/' in url)):
                        item.setProperty('IsPlayable', 'true')
                        xbmcplugin.addDirectoryItem(self.handle, uri, item, False)
                    else:
                        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
            else:
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        if not items_count < 16:
            uri = sys.argv[0] + '?mode=%s&url=%s&page=%s' % ("index", url, str(int(page) + 1))
            item = xbmcgui.ListItem(self.language(1004), iconImage=self.inext)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'movies')
        xbmcplugin.endOfDirectory(self.handle, True)
        xbmc.log('HDREZKA: end index', xbmc.LOGNOTICE)

    def selectQuality(self, links, title, image, subtitles = None):
        list = sorted(links.iteritems(), key=itemgetter(0))
        i = 0
        for quality, link in list:
            i += 1
            if self.quality != 'select':
                if quality > int(self.quality[:-1]):
                    self.play(links[quality_prev], title, image, subtitles)
                    break
                elif (len(list) == i):
                    self.play(links[quality], title, image, subtitles)
            else:
                film_title = "%s (%s)" % (title, str(quality) + 'p')
                uri = sys.argv[0] + '?mode=play&url=%s' % urllib.quote(link)
                item = xbmcgui.ListItem(film_title, iconImage=image)
                item.setInfo(type='Video', infoLabels={'title': film_title, 'overlay': xbmcgui.ICON_OVERLAY_WATCHED, 'playCount': 0})
                item.setProperty('IsPlayable', 'true')
                if subtitles: 
                    item.setSubtitles([subtitles])
                xbmcplugin.addDirectoryItem(self.handle, uri, item, False)
            quality_prev = quality

    def selectTranslator(self, content, post_id):
        iframe0 = common.parseDOM(content, 'iframe', ret='src')[0]
        usr_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0'
        try:
            playlist0 = common.parseDOM(content, "ul", attrs={"class": "b-simple_episodes__list clearfix"})
        except:
            playlist0 = ""  
        try:
            div = common.parseDOM(content, 'ul', attrs={'id': 'translators-list'})[0]
        except:
            return iframe0, playlist0
        titles = common.parseDOM(div, 'li')
        ids = common.parseDOM(div, 'li', ret = "data-translator_id")
        if len(titles) > 1:
            dialog = xbmcgui.Dialog()
            index_ = dialog.select(self.language(1006), titles)
            if int(index_) < 0:
                index_ = 0    
        else:
            index_ = 0    
        idt = ids[index_]

        headers = {
            "Host": self.domain,
            "Origin": self.url,
            "User-Agent": usr_agent,
            "X-Requested-With": "XMLHttpRequest"
        }

        values = {
            "id": post_id,
            "translator_id": idt
        }

        request = urllib2.Request(self.url + "/ajax/get_cdn_series/", urllib.urlencode(values), headers)
        response = urllib2.urlopen(request).read()

        data = json.loads(response)
        player = data["player"]
        seasons = data["seasons"]
        episodes = data["episodes"]
        iframe = common.parseDOM(player, 'iframe', ret='src')[0]
        playlist = common.parseDOM(episodes, "ul", attrs={"class": "b-simple_episodes__list clearfix"})
        return iframe, playlist


    def show(self, url):
        print "Get video %s" % url
        response = common.fetchPage({"link": url})

        content = common.parseDOM(response["content"], "div", attrs={"id": "wrapper"})
        image_container = common.parseDOM(content, "div", attrs={"class": "b-sidecover"})
        title = common.parseDOM(content, "h1")[0]
        image = common.parseDOM(image_container, "img", ret='src')[0]
        post_id = common.parseDOM(content, "input", attrs={"id": "post_id" }, ret="value")[0]

        playlist = common.parseDOM(content, "ul", attrs={"class": "b-simple_episodes__list clearfix"})
        iframe = common.parseDOM(content, 'iframe', ret='src')[0]
        if playlist:
            if self.translator == "select":
                iframe, playlist = self.selectTranslator(content, post_id)
            titles = common.parseDOM(playlist, "li")
            ids = common.parseDOM(playlist, "li", ret='data-id')
            seasons = common.parseDOM(playlist, "li", ret='data-season_id')
            episodes = common.parseDOM(playlist, "li", ret='data-episode_id')

        print "POST ID %s " % post_id
        #print "Image %s" % image

        if playlist:
            #print "This is a season"
            videoplayer = common.parseDOM(content, 'div', attrs={'id': 'videoplayer'})
            for i, title in enumerate(titles):
                title = "%s (%s %s)" % (title, self.language(1005), seasons[i])
                url_episode = iframe.split("?")[0]
                uri = sys.argv[0] + '?mode=play_episode&url=%s&urlm=%s&post_id=%s&season_id=%s&episode_id=%s&title=%s&image=%s' % (url_episode, url, ids[i], seasons[i], episodes[i], title, image)
                item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
                item.setInfo('video', { 'mediatype': 'episode' })
                if self.quality != 'select':
                    item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True if self.quality == 'select' else False)
        else:
            try:
                link = self.get_video_link(url, post_id)

                uri = sys.argv[0] + '?mode=play&url=%s' % urllib.quote(link)
                item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
                item.setInfo(type='Video', infoLabels={'title': title, 'overlay': xbmcgui.ICON_OVERLAY_WATCHED, 'playCount': 0})
                item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(self.handle, uri, item, False)

            except:
                print "GET LINK FROM IFRAME"
                videoplayer = common.parseDOM(content, 'div', attrs={'id': 'videoplayer'})
                iframe = common.parseDOM(content, 'iframe', ret='src')[0]
                try:
                    links, subtitles = self.get_video_link_from_iframe(iframe, url)
                except:
                    self.getkeys_value()
                    links, subtitles = self.get_video_link_from_iframe(iframe, url)
                self.selectQuality(links, title, image)

        xbmcplugin.setContent(self.handle, 'episodes')
        xbmcplugin.endOfDirectory(self.handle, True)

    def get_item_description(self, referer, post_id):
        if self.description == "false":
            return { 'rating' : '', 'description' : '' }

        url = self.url + '/engine/ajax/quick_content.php'
        usr_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0'

        headers = {
            "Accept" : "text/plain, */*; q=0.01",
            "Content-Type" : "application/x-www-form-urlencoded; charset=UTF-8",
            "Host" : self.domain,
            "Referer" : referer,
            "User-Agent": usr_agent,
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = urllib.urlencode({
            "id" : post_id,
            "is_touch" : 0
        })

        request = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(request).read()

        description = common.parseDOM(response, 'div', attrs={'class': 'b-content__bubble_text'})[0]

        try:
            imbd_rating = common.parseDOM(response, 'span', attrs={'class': 'imdb'})[0]
            rating = common.parseDOM(imbd_rating, 'b')[0]
        except IndexError, e:
            try:
                imbd_rating = common.parseDOM(response, 'span', attrs={'class': 'kp'})[0]
                rating = common.parseDOM(imbd_rating, 'b')[0]
            except IndexError, e:
                rating = 0

        return { 'rating' : rating, 'description' : description }


    def get_video_link_from_iframe(self, url, mainurl):

        playlist_domain = 'streamblast.cc'
        playlist_domain2 = 'buchome.com'
        usr_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'

        headers = {
            "User-Agent": usr_agent,
            "Referer": mainurl
        }
        request = urllib2.Request(url, "", headers)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request).read()

        src_urljs = "http://" + playlist_domain2 + response.split('<script src="')[-1].split('"></script>')[0]
        video_token = response.split("video_token: '")[-1].split("',")[0]
        partner_id = response.split("partner_id: ")[-1].split(",")[0] 
        domain_id = response.split("domain_id: ")[-1].split(",")[0]
        ref = re.compile('ref: \'(.+?)\'').findall(response)[0]

        headers = {
            "User-Agent": usr_agent,
            "Referer": url
        }
        request = urllib2.Request(src_urljs, "", headers)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request).read()

        subtitles = None
        if 'subtitles: {"master_vtt":"' in response:
            subtitles = response.split('subtitles: {"master_vtt":"')[-1].split('"')[0]

        values = {}
        attrs = {}
        attrs['purl'] = "/vs"
        values["ref"] = ref

        raw_passkey = None
        raw_ivkey = None

        if not os.path.isfile(self.keyfile):
            self.getkeys_value()

        with open(self.keyfile, 'r') as keys_file:
            for line in keys_file:
                if "value1" in line:
                    raw_passkey = line.split("value1=")[1].strip()
                if "value2" in line:
                    raw_ivkey = line.split("value2=")[1]
                    break

        passkey = unhexlify(raw_passkey)
        ivkey = unhexlify(raw_ivkey)        

        msg = '{"a":%s,"b":"%s","c":true,"e":"%s","f":"%s"}' % (partner_id, domain_id, video_token, usr_agent)
        cipher = Cipher(alg='aes_256_cbc', key=passkey, iv=ivkey, op=1)
        ciphertext = cipher.update(msg) + cipher.final()
        values['q'] = b64encode(ciphertext)

        headers = {
            "Host": playlist_domain2,
            "Origin": "http://" + playlist_domain2,
            "User-Agent": usr_agent,
            "Referer": "http://" + playlist_domain2 + "/video/" + video_token + "/iframe",
            "X-Requested-With": "XMLHttpRequest"
        }

        request = urllib2.Request('http://' + playlist_domain2 + attrs["purl"], urllib.urlencode(values), headers)
        request.get_method = lambda: 'POST'
        response = urllib2.urlopen(request).read()

        data = json.loads(response.decode('unicode-escape'))
        playlisturl = data['m3u8']

        headers = {
            "Host": playlist_domain,
            "Origin": "http://" + playlist_domain2,
            "User-Agent": usr_agent
        }

        request = urllib2.Request(playlisturl, "", headers)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request).read()

        urls = re.compile("http:\/\/.*?\n").findall(response)
        manifest_links = {}
        for i, url in enumerate(urls):
            manifest_links[QUALITY_TYPES[i]] = url.replace("\n", "")

        return manifest_links, subtitles

    def get_video_link(self, referer, post_id):
        url = self.url + '/ajax/getvideo.php'
        usr_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0'

        headers = {
            "Accept" : "text/plain, */*; q=0.01",
            "Content-Type" : "application/x-www-form-urlencoded; charset=UTF-8",
            "Host" : self.domain,
            "Referer" : referer,
            "User-Agent": usr_agent,
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = urllib.urlencode({
            "id" : post_id
        })

        request = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(request)

        response = json.loads(response.read().encode("utf-8"))
        links = json.loads(response['link'].encode("utf-8"))
        return links['hls']

    def get_seaons_link(self, referer, video_id, season, episode):
        url = self.url + '/engine/ajax/getvideo.php'
        usr_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0'

        headers = {
            "Accept" : "text/plain, */*; q=0.01",
            "Content-Type" : "application/x-www-form-urlencoded; charset=UTF-8",
            "Host" : self.domain,
            "Referer" : referer,
            "User-Agent": usr_agent,
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = urllib.urlencode({
            'id': video_id,
            'season':  season,
            'episode': episode
        })

        request = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(request)

        response = json.loads(response.read().encode("utf-8"))
        links = json.loads(response['link'].encode("utf-8"))
        return links['hls']

    def getUserInput(self):
        kbd = xbmc.Keyboard()
        kbd.setDefault('')
        kbd.setHeading(self.language(1000))
        kbd.doModal()
        keyword = None

        if kbd.isConfirmed():
            if self.addon.getSetting('translit') == 'true':
                keyword = translit.rus(kbd.getText())
            else:
                keyword = kbd.getText()
        return keyword

    def search(self, keyword, external):
        print "*** Search"

        keyword = keyword if (external != None) else self.getUserInput()
        keyword = translit.rus(keyword) if (external == 'unified') else urllib.unquote_plus(keyword)
        unified_search_results = []

        if keyword:
            print keyword

            headers = {
                'Host': self.domain,
                'Referer': self.url,
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
            }

            values = {
                "do": "search",
                "subaction": "search",
                "q": unicode(keyword)
            }

            form = urllib.urlencode(values)
            encoded_kwargs = urllib.urlencode(values.items())
            argStr = "/?%s" %(encoded_kwargs)
            request = urllib2.Request(self.url + argStr, "", headers)
            request.get_method = lambda: 'GET'
            response = urllib2.urlopen(request).read()

            content = common.parseDOM(response, "div", attrs={"class": "b-content__inline_items"})
            videos = common.parseDOM(content, "div", attrs={"class": "b-content__inline_item"})

            for i, videoitem in enumerate(videos):
                link = common.parseDOM(videoitem, "a", ret='href')[0]
                title = common.parseDOM(videoitem, "a")[1]
                
                image = common.parseDOM(videoitem, "img", ret='src')[0]
                descriptiondiv = common.parseDOM(videoitem, "div", attrs={"class": "b-content__inline_item-link"})[0]
                description = common.parseDOM(descriptiondiv, "div")[0]

                if (external == 'unified'):
                    print "Perform unified search and return results"
                    unified_search_results.append({'title':  title, 'url': link, 'image': image, 'plugin': self.id})
                else:
                    uri = sys.argv[0] + '?mode=show&url=%s' % urllib.quote(link)
                    item = xbmcgui.ListItem("%s [COLOR=55FFFFFF][%s][/COLOR]" % (title, description), iconImage=image, thumbnailImage=image)
                    item.setInfo(type='Video', infoLabels={'title': title})
                    if (self.quality != 'select') and (not ('/series/' in link)) and (not ('/show/' in link)) and (not ('/cartoons/' in link)):
                        item.setProperty('IsPlayable', 'true')
                        xbmcplugin.addDirectoryItem(self.handle, uri, item, False)
                    else:
                        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

            if (external == 'unified'):
                UnifiedSearch().collect(unified_search_results)
            else:
                xbmcplugin.setContent(self.handle, 'movies')
                xbmcplugin.endOfDirectory(self.handle, True)
        else:
            self.menu()

    def play(self, url, title, image, subtitles = None):
        item = xbmcgui.ListItem(path = url, iconImage=image)
        item.setInfo(type='Video', infoLabels={'title': title, 'overlay': xbmcgui.ICON_OVERLAY_WATCHED, 'playCount': 0})
        if subtitles:
            urls = re.compile('http:\/\/.*?\.srt').findall(subtitles)
            item.setSubtitles(urls)
        xbmcplugin.setResolvedUrl(self.handle, True, item)

    def play_episode(self, url, referer, post_id, season_id, episode_id, title, image):
        print "***** play_season"
        try:
            url = self.get_seaons_link(referer, post_id, season_id, episode_id)

            item = xbmcgui.ListItem(path = url)
            xbmcplugin.setResolvedUrl(self.handle, True, item)

        except:
            print "GET LINK FROM IFRAME"
            url_episode = url + "?nocontrols=1&season=%s&episode=%s" % (season_id, episode_id)
            try:
                links, subtitles = self.get_video_link_from_iframe(url_episode, referer)
            except:
                self.getkeys_value()
                links, subtitles = self.get_video_link_from_iframe(url_episode, referer)
            self.selectQuality(links, title, image, subtitles)
            xbmcplugin.setContent(self.handle, 'episodes')
            xbmcplugin.endOfDirectory(self.handle, True)


    # XBMC helpers
    def showMessage(self, msg):
        xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("Info", msg, str(5 * 1000)))

    def showErrorMessage(self, msg):
        print msg
        xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("ERROR", msg, str(10 * 1000)))

    # Python helpers
    def encode(self, string):
        return string.decode('cp1251').encode('utf-8')

    def convert(s):
        try:
            return s.group(0).encode('latin1').decode('utf8')
        except:
            return s.group(0)

    def getkeys_value(self):
        i = 3
        while (i > 0): 
            response = common.fetchPage({"link": 'http://www.u2csp01.tk/hdrez/hdr_key.php'})
            if response["status"] == 200:
                data = response["content"]
                if data and "value1" in data:
                    with open(self.keyfile, 'w') as keys_file:
                        keys_file.write(data)
                    break  
            i-=1
            

plugin = HdrezkaTV()
plugin.main()
