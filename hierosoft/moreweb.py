# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import os
import platform
import time
import socket
import psutil
from socket import (
    getaddrinfo,
    gethostname,
)
import ipaddress
import subprocess
import shlex
import threading

if sys.version_info.major < 3:
    # FileNotFoundError = IOError
    ModuleNotFoundError = ImportError
    # NotADirectoryError = OSError

if sys.version_info.major >= 3:
    import urllib.request
    request = urllib.request
    from urllib.error import (
        HTTPError,
        URLError,
    )

    html_is_missing_a_submodule = False
    try:
        from html.parser import HTMLParser
    except ModuleNotFoundError as ex:
        html_is_missing_a_submodule = True
    if html_is_missing_a_submodule:
        import html
        # ^ Doesn't fix issue #3, but provides tracing info below.
        print("", file=sys.stderr)
        raise ModuleNotFoundError(
            "The html module is incomplete: {}"
            " If not using PyInstaller, ensure there is no extra"
            " html module (html directory or html.py file)"
            " that is not Python's builtin html/__init__.py"
            "\n\nIf using PyInstaller, you must add the following to"
            " your main py file (the file that is the first argument"
            " of the Analysis call in your spec file): "
            "\nimport html.parser\nimport html.entities"
            "".format(html.__file__)
        )
        # INFO:
        # - Adding 'parser' and 'entities' to __all__ in
        #   html/__init__.py did not solve the issue.

    from urllib.parse import urlparse, parse_qs
    from urllib.parse import quote as urllib_quote
    from urllib.parse import quote_plus as urllib_quote_plus
    from urllib.parse import urlencode
else:
    import urllib2 as urllib
    request = urllib
    from urllib2 import (
        HTTPError,
        URLError,
    )
    from HTMLParser import HTMLParser
    print("HTMLParser imported.", file=sys.stderr)
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
    number_to_place,
)


def valid_ip_address(value, allow_broadcast=False, allow_netmask=False):
    '''
    This function checks to ensure that a value is a properly formatted
    IPv4 address (not a hostname nor IPv6 address, nor malformed).

    Sequential arguments:
    value -- A number which may nor may not be an IP address, but should
        be checked whether it is.
    allow_broadcast -- Set to True to allow the address to end with
        255.

    Returns:
    None if good, otherwise an error string describing what is wrong
        with the value.
    '''
    parts = value.split(".")
    if len(parts) != 4:
        return "There were {} dots but should be 3.".format(value.count("."))
    for i in range(len(parts)):
        part = parts[i]
        if len(part) != len(part.strip()):
            return "The IP address shouldn't contain spaces."
        if len(part) == 0:
            if i == 0:
                return "The part before the 1st dot is blank."
            else:
                return (
                    "The part after the {} dot is blank."
                    "".format(number_to_place(i))
                )
        if not part.isdigit():
            return (
                "The {} part is not a number."
                "".format(number_to_place(i+1))
            )
        part_num = int(part)
        if ((i == 0) and (part_num == 255)):
            if not allow_netmask:
                return (
                    "The {} number cannot be {}."
                    "".format(number_to_place(i+1), part_num)
                )
        if ((i == 3) and (part_num == 0)):
            if not allow_netmask:
                return (
                    "The {} number cannot be {}."
                    "".format(number_to_place(i+1), part_num)
                )
        if ((i == 3) and (part_num == 255)):
            if not allow_broadcast:
                return (
                    "The {} number cannot be {}."
                    "".format(number_to_place(i+1), part_num)
                )
        if (part_num > 255) or (part_num < 0):
            return "Each part of the address must be 0 to 255."
    return None


def name_from_url(url):
    filename = url
    slash_i = url.rfind("/")
    if slash_i >= 0:
        filename = url[slash_i+1:]
    return filename


STATUS_DONE = "done"
STATUS_RESPONSE = "response"


def get_ips(ip_addr_proto="ipv4", ignore_local=True, ignore_unassigned=True):
    '''
    Get the IP address(es) of the local machine (the computer running
    the program).

    Keyword arguments:
    ignore_local -- Ignore 127.* addresses (localhost).
    ignore_unassigned -- Ignore 169.* addresses (missing DHCP server or
        disconnected from the network).
    '''
    # import psutil  # works on Windows, macOS, and GNU/Linux systems.
    # Based on <https://stackoverflow.com/a/73559817/4541104>.
    af_inet = socket.AF_INET
    if ip_addr_proto == "ipv6":
        af_inet = socket.AF_INET6
    elif ip_addr_proto == "both":
        af_inet = 0

    results = []
    for interface, interface_addrs in psutil.net_if_addrs().items():
        if interface_addrs is None:
            echo1("There are no addresses on interface {}".format(interface))
            continue
        for snicaddr in interface_addrs:
            if snicaddr.family == af_inet:
                octet0 = snicaddr.address.split(".")[0]
                if ignore_local:
                    if octet0 == "127":
                        continue
                if ignore_unassigned:
                    if octet0 == "169":
                        continue
                # results.append(snicaddr.addressinterface_addrs)
                # ^ AttributeError
                results.append(snicaddr.address)
    return results


def UNUSABLE_get_ips(ip_addr_proto="ipv4", ignore_local=True):
    '''
    UNUSABLE: Gets only local on linux.

    By default, this method only returns non-local IPv4 addresses
    To return IPv6 only, call get_ip('ipv6')
    To return both IPv4 and IPv6, call get_ip('both')
    To return local IPs, call get_ip(None, False)
    Can combine options like so get_ip('both', False)
    '''
    # Based on <https://stackoverflow.com/a/64530508/4541104>.

    # See also ways using Python modules from PyPi:
    # - import netifaces: <https://stackoverflow.com/a/66534468/4541104>
    # - import psutil: <https://stackoverflow.com/a/73559817/4541104>

    af_inet = socket.AF_INET  # 2
    if ip_addr_proto == "ipv6":
        af_inet = socket.AF_INET6  # 30
    elif ip_addr_proto == "both":
        af_inet = 0
    hostname = gethostname()
    echo0("hostname={}".format(hostname))
    # system_ip_list = getaddrinfo(hostname, None, af_inet, 1, 0)
    system_ip_list = getaddrinfo(hostname, None, family=af_inet,
                                 proto=socket.IPPROTO_TCP)
    # ^ getaddrinfo(host, port, family=0, type=0, proto=0, flags=0)
    ip_list = []

    echo0("system_ip_list:")
    for ip in system_ip_list:
        echo0("- ip={}".format(ip))
        ip = ip[4][0]

        try:
            ipaddress.ip_address(str(ip))
            ip_address_valid = True
        except ValueError:
            ip_address_valid = False
        else:
            no_local = ignore_local
            if ((ipaddress.ip_address(ip).is_loopback and no_local)
                    or (ipaddress.ip_address(ip).is_link_local and no_local)):
                pass
            elif ip_address_valid:
                ip_list.append(ip)

    return ip_list


def get_ips(ip_addr_proto="ipv4", ignore_local_ips=True):
    '''
    Get the IP address(es) of the local machine (the computer running
    the program).
    '''
    # import psutil  # works on Windows, macOS, and GNU/Linux systems.
    # Based on <https://stackoverflow.com/a/73559817/4541104>.
    af_inet = socket.AF_INET
    if ip_addr_proto == "ipv6":
        af_inet = socket.AF_INET6
    elif ip_addr_proto == "both":
        af_inet = 0

    results = []
    for interface, interface_addrs in psutil.net_if_addrs().items():
        if interface_addrs is None:
            echo1("There are no addresses on interface {}".format(interface))
            continue
        for snicaddr in interface_addrs:
            if snicaddr.family == af_inet:
                if ignore_local_ips:
                    if snicaddr.address.split(".")[0] == "127":
                        continue
                # results.append(snicaddr.addressinterface_addrs)
                # ^ AttributeError
                results.append(snicaddr.address)
    return results


def UNUSABLE_get_ips(ip_addr_proto="ipv4", ignore_local_ips=True):
    '''
    UNUSABLE: Gets only local on linux.

    By default, this method only returns non-local IPv4 addresses
    To return IPv6 only, call get_ip('ipv6')
    To return both IPv4 and IPv6, call get_ip('both')
    To return local IPs, call get_ip(None, False)
    Can combine options like so get_ip('both', False)
    '''
    # Based on <https://stackoverflow.com/a/64530508/4541104>.

    # See also ways using Python modules from PyPi:
    # - import netifaces: <https://stackoverflow.com/a/66534468/4541104>
    # - import psutil: <https://stackoverflow.com/a/73559817/4541104>

    af_inet = socket.AF_INET  # 2
    if ip_addr_proto == "ipv6":
        af_inet = socket.AF_INET6  # 30
    elif ip_addr_proto == "both":
        af_inet = 0
    hostname = gethostname()
    echo0("hostname={}".format(hostname))
    # system_ip_list = getaddrinfo(hostname, None, af_inet, 1, 0)
    system_ip_list = getaddrinfo(hostname, None, family=af_inet,
                                 proto=socket.IPPROTO_TCP)
    # ^ getaddrinfo(host, port, family=0, type=0, proto=0, flags=0)
    ip_list = []

    echo0("system_ip_list:")
    for ip in system_ip_list:
        echo0("- ip={}".format(ip))
        ip = ip[4][0]

        try:
            ipaddress.ip_address(str(ip))
            ip_address_valid = True
        except ValueError:
            ip_address_valid = False
        else:
            if ipaddress.ip_address(ip).is_loopback and ignore_local_ips or ipaddress.ip_address(ip).is_link_local and ignore_local_ips:
                pass
            elif ip_address_valid:
                ip_list.append(ip)

    return ip_list


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


# See <https://stackoverflow.com/a/27767560/4541104>:
# chunk_size was 1024 in Python 2 example, and 4096 in the Python 3
# example.
def netcat(host, port, content, cb_progress=None, cb_done=None,
           evt=None, chunk_size=1024, path=None):
    '''
    For documentation, see sys_netcat.
    '''
    chunk_size = int(chunk_size)
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

    if evt.get('connection_timeout') is not None:
        s.settimeout(int(evt['connection_timeout']))
        evt['status'] = (
            'connecting (timeout="{}")...'.format(evt['connection_timeout'])
        )
    else:
        evt['status'] = "connecting..."
    cb_progress(evt)
    s.connect((host, int(port)))
    if sys.version_info.major >= 3:
        if not isinstance(content, bytes):
            content = content.encode()
    # s.sendall(content)

    if evt.get('send_timeout') is not None:
        s.settimeout(int(evt['send_timeout']))

    sendall(
        s,
        content,
        cb_progress=cb_progress,
        cb_done=cb_done,  # cb_done is called twice, with STATUS_DONE and below
        evt=evt,
    )
    # ^ sendall keeps calling s.send until all data is sent or there
    #   is an exception (See
    #   <https://stackoverflow.com/a/34252690/4541104>).
    evt['status'] = "waiting to shutdown socket..."
    cb_progress(evt)
    time.sleep(0.5)
    # sleep may or may not help. See tripleee's
    # comment on <https://stackoverflow.com/a/27767560/4541104>.
    evt['status'] = "shutdown socket..."
    cb_progress(evt)
    s.shutdown(socket.SHUT_WR)
    sys.stdout.write("Response:")
    while True:
        data = s.recv(chunk_size)
        if sys.version_info.major >= 3:
            if not data:
                break
        else:
            if len(data) == 0:
                break
        print(repr(data))
    echo0("Connection closed.")
    s.close()
    evt['status'] = STATUS_RESPONSE
    cb_done(evt)
    # cb_done is called twice, above with STATUS_DONE and again with
    # STATUS_RESPONSE.



def sys_netcat(hostname, port, content, cb_progress=None, cb_done=None,
               chunk_size=1024, evt=None, path=None):
    '''
    Send binary data to a port. The sys_netcat function (and not other
    netcat functions) uses the system's netcat shell command (generally
    not available on Windows). The netcat functions and sys_netcat
    function emulate the following except accept data (bytes object)
    instead of a path:

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
        - connection_timeout -- Set the timeout in seconds for the
          connection (only applies to netcat function, not sys_netcat
          function).
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

    Raises
    urllib.error.URLError -- (or on Python 2, urllib2.URLError)
        (access either using `from hierosoft.moreweb import URLError`)
        if there is no connection to the host. The Exception is
        raised by the Python request module.
    '''

    '''
    if total_bytes is not None:
        echo0("Warning: total_bytes is deprecated in the download"
              " method. Set evt['total_size'] instead.")
        evt['total_size'] = total_size
    '''
    echo0("* downloading {}".format(url))

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
    except URLError as ex:
        evt['error'] = str(ex)
        cb_done(evt)
        return
    # ^ raises urllib.error.URLError (or Python 2 urllib2.URLError)
    #   if not connected to the internet
    #   ("urllib.error.URLError: <urlopen error [Errno 11001] getaddrinfo failed")
    # ^ raises urllib.error.HTTPError (or Python 2 urllib2.HTTPError)
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
        # echo0("* writing")
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
        self.download_thread = None

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
            echo0("download_thread is already running for {}".format(self.host))
            return False
        self.download_thread = threading.Thread(
            target=download,
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
