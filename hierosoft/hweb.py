# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import os
import platform

if sys.version_info.major >= 3:
    import urllib.request
    request = urllib.request
    from urllib.error import HTTPError
    from html.parser import HTMLParser
    from urllib.parse import urlparse, parse_qs
    from urllib.parse import quote as urllib_quote
    from urllib.parse import quote_plus as urllib_quote_plus
    from urllib.parse import urlencode
else:
    import urllib2 as urllib
    request = urllib
    from urllib2 import HTTPError
    from HTMLParser import HTMLParser
    from urlparse import urlparse, parse_qs
    from urllib import quote as urllib_quote
    from urllib import quote_plus as urllib_quote_plus
    from urllib import urlencode

'''
# url parsing example:
url = "https://example.com?message=hi%20there"
parsed_url = urlparse(url)
# ^ ParseResult(scheme='https', netloc='example.com', path='',
#   params='', query='message=hi%20there', fragment='')
params = parse_qs(parsed_url.query)
# ^ {'value': ['hi there']}

The examples below are from <https://www.urlencoder.io/python/>.

# url encoding example:
urllib_quote("hi there")
# ^ "hi%20there"
urllib_quote_plus(query)
# ^ "hi+there" (use '+' instead of %20 for space)

# Encoding multiple parameters at once
params = {'q': 'Python URL encoding', 'message': 'hi there'}
urlencode(params)
# ^ 'q=Python+URL+encoding&message=hi+there' (uses '+' on Python 2 or 3)
'''


from hierosoft import (
    echo0,
    echo1,
    echo2,
    HOME,
    LOCALAPPDATA,
    APPDATA,
    SHORTCUT_EXT,
)


def name_from_url(url):
    filename = url
    slash_i = url.rfind("/")
    if slash_i >= 0:
        filename = url[slash_i+1:]
    return filename


# create a subclass and override the handler methods
class DownloadPageParser(HTMLParser):
    HELP = {
        # formerly self.linArch, self.darwinArch, self.winArch,
        #   self.release_version, self.platform_flag, self.release_arch:
        'version': "Gather only files that are this version.",
        'platform': "Gather only files with this platform substring.",
        'arch': ("Gather only files that are marked as this architecture"
                 " (such as linux64, x86_64, arm, or another"
                 " custom arch string specific to that software)."),
        'must_contain': "Only collect file URLs with this substring.",
    }

    @classmethod
    def get_option_keys(cls):
        return list(cls.HELP.keys())

    @classmethod
    def get_help(cls, key):
        return HELP.get(key)

    def set_options(self, options):
        for key, value in options.items():
            if key not in DownloadPageParser.get_option_keys():
                echo0('[DownloadPageParser] Warning: The option {} is not valid'
                      ''.format(key))
            self.options[key] = value

    def get_option(self, key):
        return self.options.get(key)

    def __init__(self, options):
        # avoid "...instance has no attribute rawdata":
        #   Old way:
        #     HTMLParser.__init__(self)
        #   On the next commented line, python2 would say:
        #       "argument 1 must be type, not classobj"
        #     super(DownloadPageParser, self).__init__()
        if sys.version_info.major >= 3:
            super().__init__()
            # print("Used python3 super syntax")
        else:
            # python2
            HTMLParser.__init__(self)
            # print("Used python2 super syntax")
        self.options = {}
        self.set_options(options)

        self.urls = []
        self.tag = None
        self.tag_stack = []
        self.archive_categories = {}  # based on install_any.py
        self.archive_categories["tar"] = [".tar.bz2", ".tar.gz",
                                          ".tar.xz"]
        self.blender_redir = "https://www.blender.org/download/release"
        self.blender_mirror = "https://mirrors.ocf.berkeley.edu/blender/release"
        # TODO:
        #         https://www.blender.org/download/release/Blender3.3/blender-3.3.1-linux-x64.tar.xz/
        # becomes
        # https://mirrors.ocf.berkeley.edu/blender/release/Blender3.3/blender-3.3.1-linux-x64.tar.xz
        self.archive_categories["zip"] = [".zip"]
        self.archive_categories["dmg"] = [".dmg"]
        self.extensions = []
        for category, endings in self.archive_categories.items():
            self.extensions.extend(endings)
        self.closers = ["-glibc"]
        self.openers = ["blender-"]
        self.remove_this_dot_any = ["-10."]
        # self.os_release = platform.release()
        # ^ such as '5.10.0-18-amd64' on linux

    def handle_decl(self, decl):
        self.urls = []
        print("CLEARED dl list since found document decl: " + decl)

    def handle_starttag(self, tag, attrs):
        must_contain = self.get_option('must_contain')
        if tag.lower() == "html":
            self.urls = []
            print("CLEARED dl list since found <html...")
            # print('Links:  # with "{}"'.format(must_contain))
        echo2(" " * len(self.tag_stack) + "push: " + str(tag))
        self.tag_stack.append(tag)
        # attrs is an array of (name, value) tuples:
        attr_d = dict(attrs)
        href = attr_d.get("href")
        raw_href = href
        if href is not None:
            if href.startswith(self.blender_redir) and href.endswith("/"):
                # TODO: ^ Never occurs since apparently JavaScript loads
                #   this html? There is no "matches" nor "not match"
                #   showing below for 3.3.1.
                href = self.blender_mirror + href[len(self.blender_redir):]
                if href.endswith("/"):
                    href = href[:-1]
                    # Change .xz/ to .xz since .xz/ denotes a redirect.
                echo1('href {} became {}'.format(raw_href, href))
            if (must_contain is None) or (must_contain in href):
                echo1("  - (matches {}) {}".format(must_contain, href))
                if href not in self.urls:
                    if not href.lower().endswith("sha256"):
                        self.urls.append(href)
            else:
                echo1('  - (does not match "{}") {}'.format(must_contain, href))
        echo2(" " * len(self.tag_stack) + "attr_d: " + str(attr_d))

        self.tag = tag

    def handle_endtag(self, tag):
        if tag.lower() != self.tag_stack[-1].lower():
            found = None
            for i in range(1, len(self.tag_stack)+1):
                if tag.lower() == self.tag_stack[-i].lower():
                    found = i
                    break
            if found is not None:
                for i in range(found, len(self.tag_stack)+1):
                    echo2(" " * len(self.tag_stack)
                          + "unwind: (" + self.tag_stack[-1]
                          + " at ) " + str(tag))
                    self.tag_stack.pop()
            else:
                echo2(" " * len(self.tag_stack) + "UNEXPECTED: " + str(tag))
        else:
            self.tag_stack.pop()
            echo2(" " * len(self.tag_stack) + ":" + str(tag))

    def handle_data(self, data):
        echo2(" " * len(self.tag_stack) + "data:" + str(data))

    def id_from_name(self, filename, remove_arch=True,
                     remove_win_arch=False, remove_ext=False,
                     remove_openers=True, remove_closers=True):
        '''
        Get the id from the filename. This uses the following keys from
        options: version, platform, arch. Arch can be a string or list
        of strings.
        '''
        only_v = self.options.get('version')
        only_p = self.options.get('platform')
        only_a = self.options.get('arch')
        ret = filename
        if remove_openers:
            for opener in self.openers:
                # ret = ret.replace(opener, "")
                o_i = ret.find(opener)
                if o_i == 0:
                    ret = ret[len(opener):]
        # only remove platform and arch if not Windows since same
        # (only way to keep them & allow installing 64&32 concurrently)
        if only_p is not None:
            if remove_win_arch or ("win" not in only_p.lower()):
                ret = ret.replace("-"+only_p, "")
        if only_a is not None:
            arches = [only_a]
            if isinstance(only_a, list):
                arches = only_a
            for arch in arches:
                if remove_win_arch or ("win" not in arch.lower()):
                    ret = ret.replace("-"+arch, "")
        if remove_closers:
            for closer in self.closers:
                c_i = ret.find(closer)
                if c_i > -1:
                    next_i = -1
                    dot_i = ret.find(".", c_i+1)
                    hyphen_i = ret.find("-", c_i+1)
                    if dot_i > -1:
                        next_i = dot_i
                    if hyphen_i > -1:
                        if next_i > -1:
                            if hyphen_i < next_i:
                                next_i = hyphen_i
                        else:
                            next_i = hyphen_i
                    if next_i > -1:
                        # don't remove extension or other chunks
                        ret = ret[:c_i] + ret[next_i:]
                    else:
                        ret = ret[:c_i]
                    break
        for rt in self.remove_this_dot_any:
            for i in range(0, 99):
                osx = rt + str(i)
                ext_i = ret.find(osx)
                if ext_i > -1:
                    ret = ret[:ext_i]
                    break
        if remove_ext:
            for ext in self.extensions:
                ext_i = ret.find(ext)
                if ext_i > -1:
                    ret = ret[:ext_i]
        return ret

    def id_from_url(self, url, remove_arch=True,
                    remove_win_arch=False, remove_ext=False,
                    remove_openers=True, remove_closers=True):
        filename = name_from_url(url)
        return self.id_from_name(
            filename,
            remove_arch=remove_arch,
            remove_win_arch=remove_win_arch,
            remove_ext=remove_ext,
            remove_openers=remove_openers,
            remove_closers=remove_closers
        )

    def blender_tag_from_url(self, url):
        tag_and_commit = self.id_from_url(url, remove_ext=True)
        h_i = tag_and_commit.find("-")
        version_s = tag_and_commit
        if h_i > -1:
            version_s = tag_and_commit[:h_i]
        return version_s

    def blender_commit_from_url(self, url):
        tag_and_commit = self.id_from_url(url, remove_ext=True)
        h_i = tag_and_commit.find("-")
        commit_s = tag_and_commit
        if h_i > -1:
            commit_s = tag_and_commit[h_i+1:]
        return commit_s


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
        self.profile_path = HOME
        self.localappdata_path = LOCALAPPDATA
        self.appdata_path = APPDATA
        self.parser = None

    def set_options(self, options):
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
        return SHORTCUT_EXT

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
        # print("GOT:" + dat)
        # Decode dat to avoid error on Python 3:
        #   htmlparser self.rawdata  = self.rawdata + data
        #   TypeError: must be str not bytes
        self.parser.feed(dat.decode("UTF-8"))
        return self.parser.urls

    def download(self, stream, url, cb_progress=None, cb_done=None,
                 chunk_len=16*1024, total_bytes=None):
        '''
        Sequential arguments:
        stream -- This is assumed to be an open stream (or any other
            class) on which *binary* "write" can be called, for writing
            binary data directly from the internet address. If it is
            a file stream, open with the 'wb' mode.
        url -- The internet address to read.

        Keyword arguments:
        cb_progress -- The callback (function) that receives the amount
            of data read so far. It must receive an event in the form of
            a dictionary as the only argument.
        cb_done -- The callback (function) that is called when the
            download has completed. It must receive an event in the form
            of a dictionary as the only argument.
        chunk_len -- The chunk size for reading data from the URL.
        total_bytes -- If not None, the callbacks will not only receive
            the number of bytes written ('loaded') but also 'ratio'
            based on this denominator.
        '''
        self.total_bytes = total_bytes
        self.url = url
        # based on code from blendernightly with permission from Jake Gustafson
        evt = {}
        evt['loaded'] = 0
        evt['url'] = self.url
        try:
            response = request.urlopen(self.url)
        except HTTPError as ex:
            evt['error'] = str(ex)
            if cb_done is not None:
                cb_done(evt)
            return
        # ^ raises urllib.error.HTTPError (or Python 2 HTTPError)
        #   in case of "HTTP Error 404: Not Found"
        # evt['total'] is not implemented (would be from contentlength
        # aka content-length)
        # with open(file_path, 'wb') as f:
        while True:
            chunk = response.read(chunk_len)
            if not chunk:
                break
            evt['loaded'] += chunk_len
            if self.total_bytes is not None:
                evt['ratio'] = float(evt['loaded']) / float(self.total_bytes)
            if cb_progress is not None:
                cb_progress(evt)
            stream.write(chunk)
        if cb_done is not None:
            cb_done(evt)

    def get_downloads_path(self):
        return os.path.join(self.profile_path, "Downloads")

    def get_desktop_path(self):
        return os.path.join(self.profile_path, "Desktop")

    def absolute_url(self, rel_href):
        route_i = rel_href.find("//")
        html_url = self.options.get('html_url')
        print("REL: " + rel_href)
        print("HTML: " + html_url)
        relL = rel_href.lower()
        if relL.startswith("https://") or relL.startswith("http://"):
            return rel_href
        if route_i > -1:
            # assume before '//' is route (not real directory) & remove:
            rel_href = rel_href[route_i+2:]
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
                # print("FIRST_WORD: " + first_word)
                redundant_flags.append(first_word)
                redundant_flags.append(first_word + "/")

        # if first word of subdir is in root dir, assume redundant:
        for flag in redundant_flags:
            route_i = rel_href.find(flag)
            if route_i > -1:
                if html_url[-len(flag):] == flag:
                    # assume is route (not real directory) & remove:
                    rel_href = rel_href[route_i+len(flag):]
                    print("NEW_REL: " + rel_href)
        if (html_url[-1] == "/") and (rel_href[0] == "/"):
            start = 1
            if rel_href[1] == "/":
                start = 2
            rel_href = rel_href[start:]
        return html_url + rel_href


if __name__ == "__main__":
    print("You must import this module and call get_meta() to use it")
