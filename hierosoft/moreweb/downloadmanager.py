import os
import threading

from hierosoft import (  # noqa F401
    echo0,
    echo1,
    echo2,
    sysdirs,
    write0,
    write1,
    write2,
)

from hierosoft.moreweb import (
    download,
    request,
)

from hierosoft.moreweb.downloadpageparser import DownloadPageParser


class DownloadManager:
    '''
    Download a file and optionally scrape a web page. All of the
    option names can be listed using DownloadManager.get_option_keys().
    for documentation, see DownloadManager.get_help(key) where key is
    the option. If the option is in DownloadPageParser.get_option_keys()
    the HELP key is defined there, but get_help will still work here.
    '''
    # formerly blendernightly LinkManager (moved to hierosoft by author).
    # TODO: If there are helpful changes in
    #   ~/git/linux-preinstall/everyone/deprecated/LBRY-AppImage.py
    #   then merge them.
    # - Another variant (of the old file_path version of download) is
    #   in <https://github.com/poikilos/nopackage>.

    HELP = {
        'html_url': "Scrape this web page (only for get_urls method).",
        'base_url': "Prepend this instead of html_url to found relative URL",
    }  # For further options see DownloadPageParser's get_help

    @classmethod
    def get_option_keys(cls):
        return list(cls.HELP.keys()) + DownloadPageParser.get_option_keys()

    @classmethod
    def get_help(cls, key):
        if key in DownloadPageParser.get_option_keys():
            return DownloadPageParser.get_help(key)
        return cls.HELP.get(key)

    def __init__(self):
        self.options = {}
        # self.set_options(options)
        self.profile_path = sysdirs['HOME']
        self.localappdata_path = sysdirs['LOCALAPPDATA']
        self.appdata_path = sysdirs['APPDATA']
        self.parser = None
        self.download_thread = None
        self.url = None

    def set_mgr_and_parser_options(self, options):
        """Set options that apply to DownloadManager and DownloadPageParser.

        Args:
            options (dict): options that apply to this and parser
        """
        if self.parser is None:
            self.parser = DownloadPageParser(self.options)
        for key, value in options.items():
            if key in DownloadPageParser.get_option_keys():
                # Send a matching option to DownloadPageParser
                self.parser.set_options({key: value})
                continue
            if key not in DownloadManager.get_option_keys():
                echo0('[DownloadManager] Warning: The option {} is invalid'
                      ''.format(key))
            self.options[key] = value

    def get_shortcut_ext(self):
        return sysdirs['SHORTCUT_EXT']

    def get_urls(self):
        if self.parser is None:
            self.parser = DownloadPageParser(self.options)
        html_url = self.options.get('html_url')
        if html_url is None:
            raise ValueError("html_url is None.")
        # self.parser.urls = []  # done automatically on BODY tag
        # python2 way: `urllib.urlopen(html_url)`
        response = request.urlopen(html_url)
        dat = response.read()
        # echo0("GOT:" + dat)
        # Decode dat to avoid error on Python 3:
        #   htmlparser self.rawdata  = self.rawdata + data
        #   TypeError: must be str not bytes
        self.parser.feed(dat.decode("UTF-8"))
        return self.parser.urls

    def download_and_wait(self, stream, url, cb_progress=None,
                          cb_done=None, chunk_size=16*1024, evt=None,
                          path=None):
        '''
        For documentation see the download function rather than the
        DownloadManager download method.
        '''
        self.url = url
        if evt is None:
            evt = {}
        self.total_size = evt.get('total_size')
        return download(stream, url, cb_progress=cb_progress, cb_done=cb_done,
                        chunk_size=chunk_size, evt=evt, path=path)

    def _download(self, stream, url, cb_progress=None,
                  cb_done=None, chunk_size=16*1024, evt=None,
                  path=None):
        '''
        For documentation see download in hierosoft.moreweb.
        '''
        try:
            download(stream, url, cb_progress=cb_progress,
                     cb_done=cb_done, chunk_size=chunk_size,
                     evt=evt, path=path)
        except Exception as ex:
            echo0("download could not finish: %s" % ex)
            self.download_thread = None
            raise
        self.download_thread = None

    def download(self, stream, url, cb_progress=None,
                 cb_done=None, chunk_size=16*1024, evt=None,
                 path=None):
        '''
        For documentation see the download function rather than the
        DownloadManager download method.
        '''
        self.url = url
        if evt is None:
            evt = {}
        self.total_size = evt.get('total_size')
        if self.download_thread is not None:
            echo0("download_thread is already running for {}".format(self.url))
            return False

        self.download_thread = threading.Thread(
            target=self._download,
            args=(stream, url,),
            kwargs={
                'cb_progress': cb_progress,
                'cb_done': cb_done,
                'evt': evt,
                'chunk_size': chunk_size,
                'path': path,
            },
        )
        echo0("* starting download thread...")
        self.download_thread.start()
        return True

    def get_downloads_path(self):
        return os.path.join(self.profile_path, "Downloads")

    def get_desktop_path(self):
        return os.path.join(self.profile_path, "Desktop")

    def absolute_url(self, rel_href):
        route_i = rel_href.find("//")
        html_url = self.options.get('html_url')
        echo0("found rel_href: " + rel_href)
        echo0("html_url: " + html_url)

        relL = rel_href.lower()
        if relL.startswith("https://") or relL.startswith("http://"):
            return rel_href
        if route_i > -1:
            # assume before '//' is route (not real directory) & remove:
            rel_href = rel_href[route_i+2:]

        base_url = self.options.get('base_url')
        if not base_url:
            base_url = html_url
        else:
            echo0("base_url: " + html_url)
            full_url = base_url
            if not full_url.endswith("/") and not rel_href.startswith("/"):
                full_url += "/"
            full_url += rel_href
            return full_url

        redundant_flags = []
        # redundant_flags = ["download", "download/"]
        slash2 = rel_href.find("/")
        if slash2 > -1:
            start = 0
            if slash2 == 0:
                start += 1
                slash2 = rel_href.find("/", start)
                if slash2 == 1:
                    start += 1
                    slash2 = rel_href.find("/", start)
            if slash2 > -1:
                first_word = rel_href[start:slash2]
                # echo1("FIRST_WORD: " + first_word)
                redundant_flags.append(first_word)
                redundant_flags.append(first_word + "/")

        # if first word of subdir is in root dir, assume redundant:
        for flag in redundant_flags:
            route_i = rel_href.find(flag)
            if route_i > -1:
                if html_url[-len(flag):] == flag:
                    # assume is route (not real directory) & remove:
                    rel_href = rel_href[route_i+len(flag):]
                    echo0("NEW_REL: " + rel_href)
        if (html_url[-1] == "/") and (rel_href[0] == "/"):
            start = 1
            if rel_href[1] == "/":
                start = 2
            rel_href = rel_href[start:]
        return html_url + rel_href
