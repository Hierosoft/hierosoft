# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import os
import platform
import time
import socket
import subprocess
import shlex

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

# The polyfills below are used in other file(s) in the module.

if sys.version_info.major >= 3:
    # from subprocess import run as sp_run

    # Globals used:
    # import subprocess
    from subprocess import CompletedProcess
    from subprocess import run as sp_run
else:
    class CompletedProcess:
        '''
        This is a Python 2 substitute for the Python 3 class.
        '''
        _custom_impl = True

        def __init__(self, args, returncode, stdout=None, stderr=None):
            self.args = args
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

        def check_returncode(self):
            if self.returncode != 0:
                err = subprocess.CalledProcessError(self.returncode,
                                                    self.args,
                                                    output=self.stdout)
                raise err
            return self.returncode

    # subprocess.run doesn't exist in Python 2, so create a substitute.
    def sp_run(*popenargs, **kwargs):
        '''
        CC BY-SA 4.0
        by Martijn Pieters
        https://stackoverflow.com/a/40590445
        and Poikilos
        '''
        this_input = kwargs.pop("input", None)
        check = kwargs.pop("handle", False)

        if this_input is not None:
            if 'stdin' in kwargs:
                raise ValueError('stdin and input arguments may not '
                                 'both be used.')
            kwargs['stdin'] = subprocess.PIPE

        process = subprocess.Popen(*popenargs, **kwargs)
        try:
            outs, errs = process.communicate(this_input)
        except Exception as ex:
            process.kill()
            process.wait()
            raise ex
        returncode = process.poll()
        # print("check: {}".format(check))
        # print("returncode: {}".format(returncode))
        if check and returncode:
            raise subprocess.CalledProcessError(returncode, popenargs,
                                                output=outs)
        return CompletedProcess(popenargs, returncode, stdout=outs,
                                stderr=errs)
    subprocess.run = sp_run
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


STATUS_DONE = "done"


def sendall(sock, data, flags=0, count=0, cb_progress=None, cb_done=None,
            evt=None):
    '''
    Send bytes gradually to show progress
    (rather than calling sock.sendall). See
    <https://stackoverflow.com/a/34252690/4541104>.

    Globals used:
    import socket
    STATUS_DONE = "done"

    Keyword arguments:
    flags -- See the socket.sendall documentation on python.org.
    count -- Leave this at 0. It will be counted automatically.
        otherwise, it will be added to the callback's count.
    cb_progress -- This function will be called if the number of
        bytes uploaded increases.
    cb_done -- This function will be called when the transfer is
        complete.
    evt -- The event. This is necessary if you want to send additional
        keys back to the callbacks such as 'url'. It is recommended for
        compatibility with download callback code, since the download
        method is coded parallel to this one. It can also have special
        keys such as:
        - total_size -- If not None, the callbacks will not only
          receive the number of bytes written ('loaded') but also
          'ratio' based on this denominator.
    '''
    if evt is None:
        evt = {}

    if cb_progress is None:
        def cb_progress(evt):
            echo0('[sendall inline cb_progress] {}'.format(evt))

    if cb_done is None:
        def cb_done(evt):
            echo0('[sendall inline cb_done] {}'.format(evt))

    ret = sock.send(data, flags)
    if ret > 0:
        count += ret
        evt['loaded'] = count
        if evt.get('total_size') is not None:
            evt['ratio'] = float(evt['loaded']) / float(evt['total_size'])
        cb_progress(evt)
        return sendall(sock, data[ret:], flags, count=count,
                       cb_progress=cb_progress, cb_done=cb_done,
                       evt=evt)
    else:
        evt['loaded'] = count
        if evt.get('total_size') is not None:
            evt['ratio'] = float(evt['loaded']) / float(evt['total_size'])
        evt['status'] = STATUS_DONE
        # ^ STATUS_DONE may be checked by caller such as the netcat
        #   netcat function in hierosoft, so set
        #   even if cb_done was None
        cb_done(evt)
        return None


if sys.version_info.major >= 3:
    # See <https://stackoverflow.com/a/27767560/4541104>:
    def netcat(host, port, content, cb_progress=None, cb_done=None,
               evt=None, chunk_size=None, path=None):
        '''
        For documentation, see sys_netcat.
        '''
        if chunk_size is not None:
            echo0("Warning: chunk_size is not implemented"
                  " in the Python 3 netcat function in hierosoft.")

        if cb_progress is None:
            def cb_progress(evt):
                echo0('[netcat python3 inline cb_progress] {}'.format(evt))

        if cb_done is None:
            def cb_done(evt):
                echo0('[netcat python3 inline cb_done] {}'.format(evt))

        if evt is None:
            evt = {}
        evt['loaded'] = 0

        url = host
        if port is not None:
            url += ":{}".format(port)
        evt['url'] = url

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        evt['status'] = "connecting..."
        cb_progress(evt)
        s.connect((host, int(port)))
        if not isinstance(content, bytes):
            content = content.encode()
        # s.sendall(content)
        url = host
        if port is not None:
            url += ":{}".format(port)
        evt['url'] = url
        sendall(s, content, cb_progress=cb_progress, cb_done=cb_done, evt=evt)
        # ^ sendall keeps calling s.send until all data is sent or there
        #   is an exception (See
        #   <https://stackoverflow.com/a/34252690/4541104>).
        evt['status'] = "waiting to shutdown socket..."
        cb_progress(evt)
        time.sleep(0.5)
        # sleep may or may help. See tripleee's
        # comment on <https://stackoverflow.com/a/27767560/4541104>.
        evt['status'] = "shutdown socket..."
        cb_progress(evt)
        s.shutdown(socket.SHUT_WR)
        sys.stdout.write("Response:")
        while True:
            data = s.recv(4096)
            if not data:
                break
            print(repr(data))
        echo0("Connection closed.")
        s.close()
        evt['status'] = STATUS_DONE
        cb_done(evt)
else:
    def netcat(hostname, port, content, cb_progress=None, cb_done=None,
               evt=None, chunk_size=None, path=None):
        '''
        For documentation, see sys_netcat.
        '''
        if chunk_size is not None:
            echo0("Warning: chunk_size is not implemented"
                  " in the Python 2 netcat function in hierosoft.")

        if cb_progress is None:
            def cb_progress(evt):
                echo0('[netcat python3 inline cb_progress] {}'.format(evt))

        if cb_done is None:
            def cb_done(evt):
                echo0('[netcat python3 inline cb_done] {}'.format(evt))

        if evt is None:
            evt = {}
        evt['loaded'] = 0

        url = host
        if port is not None:
            url += ":{}".format(port)
        evt['url'] = url

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((hostname, int(port)))
        # s.sendall(content)

        sendall(s, content, cb_progress=cb_progress, cb_done=cb_done, evt=evt)
        # ^ sendall keeps calling s.send until all data is sent or there
        #   is an exception (See
        #   <https://stackoverflow.com/a/34252690/4541104>).
        time.sleep(0.5)
        # sleep may or may not help. See tripleee's
        # comment on <https://stackoverflow.com/a/27767560/4541104>.
        s.shutdown(socket.SHUT_WR)
        sys.stdout.write("Response:")
        while 1:
            data = s.recv(1024)
            if len(data) == 0:
                break
            print(repr(data))
        echo0("Connection closed.")
        s.close()
        evt['status'] = STATUS_DONE
        cb_done(evt)

def sys_netcat(hostname, port, content, cb_progress=None, cb_done=None,
               chunk_size=1024, evt=None, path=None):
    '''
    Send binary data to a port. The sys_netcat function (and not other
    netcat functions) uses the system's netcat shell command. The netcat
    functions and sys_netcat function emulate the following except
    accept data (bytes object) instead of a path:

    nc -N $hostname $port < $BIN_FILE_PATH

    Sequential arguments:
    hostname -- The hostname or IP address.
    port -- The port number as an integer.
    content -- The binary data.
    cb_progress -- This function will be called with an event
        dictionary as a param whenever status is able to be updated.
    cb_done -- This function will be called if the completion or
        failure code is reached, along with setting the status to
        STATUS_DONE or a different message if failed.
    evt -- This optional event dictionary provides static data other
        than the keys that this function generates. Whatever data
        this function generates will either overwrite or appear
        alongside your custom event keys. It can also have special keys
        such as:
        - total_size --  If this is not None, this byte count will be
          used to set evt['ratio'] for cb_progress and cb_done calls.
    chunk_size -- This size of a chunk will be sent through netcat.
    path -- Provide the path to the file that is equivalent to the
        content, for logging purposes only.
    '''
    # This function is based on run_and_get_lists from "__init__.py"
    # except:
    # - generates its own cmd_parts and doesn't use collect_stderr.
    # - Writes to stdin
    # - Has special code for handling netcat (the nc command).

    '''
    if path is None:
        raise ValueError(
            "In the system version of the netcat function, the path"
            " to the binary file is required."
        )
    '''
    cmd_parts = ["nc", "-N", hostname, str(port)]
    '''
    def cb_progress_if(arg, callback=cb_progress):
        if callback is not None:
            callback(arg)

    def cb_done_if(arg, callback=cb_done):
        if callback is not None:
            callback(arg)
    '''
    outs = []
    errs = []
    # Regarding stdout, See
    #   <https://stackoverflow.com/a/7468726/4541104>
    #   "This approach is preferable to the accepted answer as it allows
    #   one to read through the output as the sub process produces it."
    #   -Hoons Jul 21 '16 at 23:19

    # Regarding stdin, see
    #   <https://stackoverflow.com/a/11831111/4541104>
    cmd = shlex.join(cmd_parts)
    if path is not None:
        cmd += ' < "{}"'.format(path)
    echo0(cmd)  # Such as "nc -N 10.0.0.1 50123"
    collect_stderr = True
    shell = True
    if shell:
        cmd_arg = shlex.join(cmd_parts)
    else:
        cmd_arg = cmd_parts
    if collect_stderr:
        sp = subprocess.Popen(
            cmd_arg,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            shell=shell,
        )
    else:
        sp = subprocess.Popen(
            cmd_arg,
            stdin=subprocess.PIPE,
            shell=shell,
        )
    # shell: Without shell=True in this case, the sp.stdin.write seems
    #   to work even though:
    #   - it doesn't (shows progress and no error).
    #   - sp.poll() is None (which indicates it is still open)
    if evt is None:
        evt = {}
    evt['loaded'] = 0
    offset = 0

    first_out = sp.poll()
    if first_out is not None:
        raise RuntimeError(
            'The process exited early: {}'.format(first_out)
        )

    this_chunk_size = chunk_size
    # this_chunk_size = len(content)
    while offset < len(content):
        if len(content) - offset < this_chunk_size:
            this_chunk_size = len(content) - offset
        evt['loaded'] = offset
        if evt.get('total_size') is not None:
            evt['ratio'] = float(evt['loaded']) / float(evt['total_size'])
        cb_progress(evt)
        sp.stdin.write(content[offset:offset+this_chunk_size])
        # ^ raises "[Errno 32] Broken pipe" if no connection
        offset += this_chunk_size

    # sp.wait()  # seems to wait forever. communicate should be enough.
    sp.stdin.close()  # nc will see that as EOF
    # (See <https://stackoverflow.com/a/13482169/4541104>).

    evt['loaded'] = offset
    evt['status'] = 'loaded all {}'.format(offset)
    cb_progress(evt)

    if sp.stdout is not None:
        for rawL in sp.stdout:
            line = rawL.decode()
            # TODO: is .decode('UTF-8') ever necessary?
            outs.append(line.rstrip("\n\r"))
    if sp.stderr is not None:
        for rawL in sp.stderr:
            line = rawL.decode()
            while True:
                bI = line.find("\b")
                if bI < 0:
                    break
                elif bI == 0:
                    echo0("WARNING: Removing a backspace from the"
                          " start of \"{}\".".format(line))
                line = line[:bI-1] + line[bI+1:]
                # -1 to execute the backspace not just remove it
            errs.append(line.rstrip("\n\r"))
    flush_more = False
    # ^ False since this causes "ValueError: flush of closed file"
    #   after running netcat code further up.
    if flush_more:
        # MUST finish to get returncode
        # (See <https://stackoverflow.com/a/16770371>):
        more_out, more_err = sp.communicate()
        if len(more_out.strip()) > 0:
            echo0("[sys_netcat] got extra stdout: {}".format(more_out))
            outs += more_out.split("\n")
        if len(more_err.strip()) > 0:
            echo0("[sys_netcat] got extra stderr: {}".format(more_err))
            errs += more_err.split("\n")

    err = ""
    for line in errs:
        if len(line.strip()) == 0:
            continue
        err += line

    if sp.returncode != 0:
        if len(err) > 0:
            evt['status'] = err
        else:
            evt['status'] = "'{}' failed.".format(shlex.join(cmd_parts))
    else:
        evt['status'] = STATUS_DONE
    cb_done(evt)
    err = ""


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
            # echo2("Used python3 super syntax")
        else:
            # python2
            HTMLParser.__init__(self)
            # echo2("Used python2 super syntax")
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
        echo0("CLEARED dl list since found document decl: " + decl)

    def handle_starttag(self, tag, attrs):
        must_contain = self.get_option('must_contain')
        if tag.lower() == "html":
            self.urls = []
            echo0("CLEARED dl list since found <html...")
            # echo0('Links:  # with "{}"'.format(must_contain))
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


def download(stream, url, cb_progress=None, cb_done=None,
             chunk_size=16*1024, evt=None, path=None):
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
    chunk_size -- The chunk size for reading data from the URL.
    evt -- Provide a dictionary with additional keys that will be
        returned along with the event dict to callbacks. It can also
        have special keys such as:
        - total_size -- If not None, the callbacks will not only
          receive the number of bytes written ('loaded') but also
          'ratio' based on this denominator.
    path -- Provide the path to the file that is equivalent to the
        content, for logging purposes only.
    '''

    '''
    if total_bytes is not None:
        echo0("Warning: total_bytes is deprecated in the download"
              " method. Set evt['total_size'] instead.")
        evt['total_size'] = total_size
    '''

    if evt is None:
        evt = {}

    if cb_progress is None:
        def cb_progress(evt):
            echo0('[sendall inline cb_progress] {}'.format(evt))

    if cb_done is None:
        def cb_done(evt):
            echo0('[sendall inline cb_done] {}'.format(evt))

    evt['loaded'] = 0
    evt['url'] = url
    try:
        response = request.urlopen(url)
    except HTTPError as ex:
        evt['error'] = str(ex)
        cb_done(evt)
        return
    # ^ raises urllib.error.HTTPError (or Python 2 HTTPError)
    #   in case of "HTTP Error 404: Not Found"
    # evt['total'] is not implemented (would be from contentlength
    # aka content-length)
    # with open(file_path, 'wb') as f:
    while True:
        chunk = response.read(chunk_size)
        if not chunk:
            break
        evt['loaded'] += chunk_size
        if evt.get('total_size') is not None:
            evt['ratio'] = float(evt['loaded']) / float(evt['total_size'])
        cb_progress(evt)
        stream.write(chunk)
    evt['status'] = STATUS_DONE
    # if evt.get('status') != STATUS_DONE:
    #     evt['status'] = "failed"
    cb_done(evt)

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
        # echo0("GOT:" + dat)
        # Decode dat to avoid error on Python 3:
        #   htmlparser self.rawdata  = self.rawdata + data
        #   TypeError: must be str not bytes
        self.parser.feed(dat.decode("UTF-8"))
        return self.parser.urls

    def download(self, stream, url, cb_progress=None, cb_done=None,
                 chunk_size=16*1024, evt=None, path=None):
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

    def get_downloads_path(self):
        return os.path.join(self.profile_path, "Downloads")

    def get_desktop_path(self):
        return os.path.join(self.profile_path, "Desktop")

    def absolute_url(self, rel_href):
        route_i = rel_href.find("//")
        html_url = self.options.get('html_url')
        echo0("REL: " + rel_href)
        echo0("HTML: " + html_url)
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


if __name__ == "__main__":
    echo0("You must import this module and call get_meta() to use it")
