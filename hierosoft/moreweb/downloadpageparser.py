# -*- coding: utf-8 -*-
import sys

from hierosoft import (
    echo0,
    echo1,
    echo2,
    echo3,
)

from hierosoft.moreweb import (
    name_from_url,
    HTMLParser,  # imported from hierosoft instead of html.parser to handle 2to3 issues
)


class DownloadPageParser(HTMLParser):
    '''subclass to override handler methods'''
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
        return cls.HELP.get(key)

    def set_options(self, options):
        prefix = "[DownloadPageParser] "
        for key, value in options.items():
            if key not in DownloadPageParser.get_option_keys():
                echo0(prefix+'Warning: The option {} is not valid'
                      ''.format(key))
            self.options[key] = value

    def get_option(self, key):
        return self.options.get(key)

    def __init__(self, options):
        # avoid "...instance has no attribute raw_data":
        #   Old way:
        #     HTMLParser.__init__(self)
        #   On the next commented line, python2 would say:
        #       "argument 1 must be type, not classobj"
        #     super(DownloadPageParser, self).__init__()
        if sys.version_info.major >= 3:
            super().__init__()
            # echo2("Used python3 super syntax")
        else:
            # python2
            HTMLParser.__init__(self)
            # echo2("Used python2 super syntax")
        self.options = {}  # replaced by *applicable* options--see set_options
        self.set_options(options)

        self.urls = []
        self.tag = None
        self.tag_stack = []
        self.archive_categories = {}  # based on install_any.py
        self.archive_categories["tar"] = [".tar.bz2", ".tar.gz",
                                          ".tar.xz"]
        self.blender_redir = "https://www.blender.org/download/release"
        self.blender_mirror = \
            "https://mirrors.ocf.berkeley.edu/blender/release"
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
        echo0("CLEARED dl list since found document decl: " + decl)

    def handle_starttag(self, tag, attrs):
        must_contain = self.get_option('must_contain')
        if tag.lower() == "html":
            self.urls = []
            echo0("CLEARED dl list since found <html...")
            # echo0('Links:  # with "{}"'.format(must_contain))
        echo3(" " * len(self.tag_stack) + "push: " + str(tag))
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
                echo1('  - (does not match "%s") %s' % (must_contain, href))
        echo3(" " * len(self.tag_stack) + "attr_d: " + str(attr_d))

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
                    echo3(" " * len(self.tag_stack)
                          + "unwind: (" + self.tag_stack[-1]
                          + " at ) " + str(tag))
                    self.tag_stack.pop()
            else:
                echo2(" " * len(self.tag_stack) + "UNEXPECTED: " + str(tag))
        else:
            self.tag_stack.pop()
            echo3(" " * len(self.tag_stack) + ":" + str(tag))

    def handle_data(self, data):
        echo3(" " * len(self.tag_stack) + "data:" + str(data))

    def id_from_name(self, filename, remove_arch=True,
                     remove_win_arch=False, remove_ext=False,
                     remove_openers=True, remove_closers=True):
        '''Get the luid from the filename.

        This uses the following keys from options: version, platform, arch.
        Arch can be a string or list of strings.
        '''
        # region values from grandparent via set_options
        #   (from mgr's parent which is HierosoftUpdate or a subclass of it)
        # only_v = self.options.get('version')
        only_p = self.options.get('platform')
        only_a = self.options.get('arch')
        # endregion values from grandparent via set_options

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
