#!/usr/bin/env python3
"""
Usage:
hgithub.py <github_user> <project_name> <asset_name> [-O <destination>]

Options:
-O <destination>          Where to save (defaults to current directory)
"""
from __future__ import print_function

import argparse
import copy
import json
import os
import platform
import shutil
import stat
import sys

from collections import OrderedDict
from datetime import datetime, timedelta

if sys.version_info.major >= 3:
    import urllib.request
    request = urllib.request
else:
    # python2
    print("* detected Python " + str(sys.version_info.major))
    import urllib2 as urllib
    request = urllib

if sys.version_info.major >= 3:
    from urllib.parse import urlparse
    # from urllib.parse import quote_plus
    from urllib.parse import urlencode
    from urllib.parse import quote
    from urllib.parse import unquote
    from urllib.error import HTTPError
    try:
        import requests
    except ImportError:
        sys.stderr.write("If you try to use a token, you must have the"
                         " requests package for python3 such as via:\n"
                         "    sudo apt-get install python3-requests")
        sys.stderr.flush()
else:
    # Python 2
    # See <https://docs.python.org/2/howto/urllib2.html>
    from urlparse import urlparse
    # from urlparse import quote_plus
    from urllib import urlencode
    from urllib import quote
    from urllib import unquote
    from urllib2 import HTTPError
    # ^ urllib.error.HTTPError doesn't exist in Python 2
    try:
        import requests
    except ImportError:
        sys.stderr.write("If you try to use a token, you must have the"
                         " requests package for python2 such as via:\n"
                         "    sudo apt-get install python-requests")
        sys.stderr.flush()

if __name__ == "__main__":
    MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
    REPO_DIR = os.path.dirname(MODULE_DIR)
    sys.path.insert(0, REPO_DIR)

if sys.version_info.major >= 3:
    from logging import getLogger
else:
    # python2
    from hierosoft.morelogging import getLogger
    # ^ TODO: Replace all this with import(s) from hierosoft.morelogging

from hierosoft import sysdirs
from hierosoft.morelogging import (
    human_readable,
)

from hierosoft.progresswriter import ProgressWriter

logger = getLogger(__name__)


def decode_safe(b):
    # from EnlivenMinetest/utilities/enissue.py
    try:
        s = b.decode()
    except UnicodeDecodeError:
        s = b.decode('utf-8')
    return s


def stream_urlopen(outs, ins, total=None, chunk_size=8192):
    """Download incrementally from one stream to another.

    Args:
        outs (writeable): bytes output stream
        ins (iterable): bytes input stream
        total (int, optional): total bytes, only for showing progress.
            Defaults to None.
        chunk_size (int, optional): Chunk size. Defaults to 8192.

    Returns:
        int: size transferred
    """
    size = 0
    pw = ProgressWriter()
    pw.hr_fn = human_readable
    while True:
        chunk = ins.read(chunk_size)
        if not chunk:
            sys.stderr.write("\nDone\n")
            sys.stderr.flush()
            break
        outs.write(chunk)
        size += len(chunk)
        pw.write(size, total)
    return size

class RepoState:
    def __init__(self, user, project):
        moregit_cache_dir = os.path.join(sysdirs['CACHES'], "moregit")
        self.user = user
        self.project = project
        self._latest_release_meta = None
        self._latest_releas_meta_src = None
        self.latest_release_url_fmt = "https://api.github.com/repos/{user}/{project}/releases/latest"

    def latest_release_url(self):
        return self.latest_release_url_fmt.format(
            user=self.user,
            project=self.project,
        )

    def get_download(self, url, token=None, text=False, path=None, total=None):
        """Download a file to memory *or* a path.

        Args:
            url (str): The URL to download.
            token (str, optional): A token for the header to assist with
                downloading. Defaults to None.
            text (bool, optional): Whether to convert bytes to text.
                Ignored if path is set. Defaults to False.
            total (int, optional): The total number of bytes, only used
                for showing a ratio downloaded.

        Returns:
            dict: Information about the download. If no 'error', one of
                the following will be set:
                - 'text'
                - 'bytes'
                - 'path' (only set if path argument was set *and* file
                  was downloaded successfully)
        """
        results = {}
        # Based on <EnlivenMinetest/utilities/enissue.py>:
        headers = {}
        req_is_complex = False
        try:
            if token is not None:
                headers['Authorization'] = "token " + token
            stream = True if path and path.strip() else False
            if path:
                if not path.strip(".."):
                    raise ValueError("The destination cannot be \"{}\""
                                     .format(path))
            size = 0
            pw = ProgressWriter()
            pw.hr_fn = human_readable
            if len(headers) > 0:
                req_is_complex = True
                res = requests.get(url, headers=headers, stream=stream)
                # res = req.urlopen(url)
                if path and path.strip():
                    part = path + ".part"
                    results['part_path'] = part
                    with open(part, mode="wb") as file:
                        for chunk in res.iter_content(chunk_size=10 * 1024):
                            file.write(chunk)
                            size += len(chunk)
                            pw.write(size, total)
                    pw.write(size, total, force=True)
                    sys.stderr.write("\nDone\n")
                    sys.stderr.flush()
                    shutil.move(part, path)
                    del results['part_path']
                    results['path'] = os.path.realpath(path)
                    sys.stderr.write("\npath=\"{}\"\n".format(path))
                    sys.stderr.flush()
                    return results
                elif text:
                    results['text'] = res.text
                else:
                    results['bytes'] = res.content
                # NOTE: In python3, res.content is in bytes
                # (<https://stackoverflow.com/a/18810889/4541104>).
            else:
                if path and path.strip():
                    part = path + ".part"
                    results['part_path'] = part

                    with open(part, "wb") as stream:
                        if sys.version_info.major >= 3:
                            with request.urlopen(url) as response:
                                size = stream_urlopen(stream, response,
                                                      total=total)
                        else:
                            # For "with" on urlopen, Python 2 says:
                            # AttributeError: addinfourl instance has no
                            #   attribute '__exit__'
                            # so:
                            response = request.urlopen(url)
                            size = stream_urlopen(stream, response,
                                                  total=total)
                    pw.write(size, total)
                    shutil.move(part, path)
                    del results['part_path']
                    results['path'] = os.path.realpath(path)
                    sys.stderr.write("\npath=\"{}\"\n".format(path))
                    sys.stderr.flush()
                    return results
                else:
                    res = request.urlopen(url)
                if text:
                    results['text'] = decode_safe(res.read())
                else:
                    results['bytes'] = res.read()

        except HTTPError as ex:
            msg = ex.reason
            if ex.code == 410:
                msg = ("{} was apparently deleted ({})."
                       .format(url, ex.reason))
                # ^ or the issue was deleted, if it was a GitHub issue
                return {
                    'error': msg,
                    'code': ex.code,
                    'reason': msg,
                    'headers': ex.headers,
                    'url': url,
                }
            # msg = str(ex) + ": " + self.rateLimitFmt.format(url)
            return {
                'error': "Downloading {} failed.".format(url),
                'code': ex.code,
                'reason': msg,
                'headers': ex.headers,
                'url': url,
            }

        return results

    def refresh_latest_release(self):
        results = {}
        # documented way:
        # curl -L \
        #     -H "Accept: application/vnd.github+json" \
        #     https://api.github.com/repos/yt-dlp/yt-dlp-nightly-builds/releases/latest \
        #     > yt-dlp-nightly-builds-latest.json
        url = self.latest_release_url()
        results = self.get_download(url, text=True)  # token = ...

        error = results.get('error')
        if error:
            results.update(results)
            logger.error(results['error'])
            return results

        self._latest_release_meta = json.loads(results['text'])
        logger.warning("OK (decoded JSON from {})".format(url))
        self._latest_releas_meta_src = url

        return results

    def download_asset(self, asset, destination_name=None):
        """Download a GitHub asset from a release.

        Args:
            asset (dict): An asset dict (usually obtained via
                list_latest_release_assets) at least containing
                'browser_download_url'
            destination_name (str, optional): Where to download the
                release asset. Defaults to None.

        Returns:
            dict: Information about the asset. 'error' is set on error,
                so check that first. If there is no 'error', the
                following will be set:
                - 'path' of downloaded file will be set if no 'error'
        """
        results = {}
        sha2_256sums_name = 'SHA2-256SUMS'
        sha2_256sums_sig_name = "SHA2-256SUMS.sig"
        sha2_512sums_name = 'SHA2-512SUMS'
        sha2_512sums_sig_name= "SHA2-512SUMS.sig"
        asset_name = asset.get('name')
        if not destination_name or not destination_name.strip():
            if not asset_name or not asset_name.strip():
                results['error'] = "There was no 'name' nor destination_name"
            destination_name = asset_name
        destination_name = destination_name.strip()
        path = destination_name
        # NOTE: asset['url'] has the same content as 'asset'
        url = asset.get('browser_download_url')
        results = self.get_download(url, text=False, path=path,
                                    total=asset.get('size'))  # token = ...
        # ^ should set path
        return results

    def download_one_asset(self, name_pattern, destination_name=None,
                           content_type=None):
        """Download a release binary.

        Args:
            name_pattern (str): Regex string to find the correct asset.
            destination_name (str, optional): Name for destination file.
                Defaults to asset name matching name_pattern.
            content_type (str, optional): Only allow this content type
                (May prevent mistakenly downloading the wrong asset).
                Leave blank to allow any. Ignored if no name_pattern.
                Defaults to "application/octet-stream".

        Raises:
            ValueError: If no name pattern

        Returns:
            dict: Information about the asset.
                - 'error' is set on error, so check that first.
                - 'destination_path' will be set if no 'error'
        """
        if not name_pattern or not name_pattern.strip():
            raise ValueError(
                "A name pattern is required to try to download one."
                " To list assets, use list_latest_release_assets"
                " with or without a name_pattern instead."
            )
        if not content_type:
            content_type = "application/octet-stream"
        results = self.list_latest_release_assets(
            name_pattern,
            content_type=content_type,
        )
        if results.get('error'):
            return results
        if not results.get('assets'):
            results = self.list_latest_release_assets(
                None,
                content_type=None,
            )
            if name_pattern:
                results['error'] = ("No assets matched the specified"
                                    " name_pattern=\"{}\"."
                                    .format(name_pattern))
            else:
                results['error'] = "There were no assets for the release."
            return results

        if len(results['assets']) == 1:
            return self.download_asset(results['assets'][0],
                                       destination_name=destination_name)
        results['error'] = (
            "There was more than one asset matching {}: {}".format(
                name_pattern,
                [asset.get('name') for asset in results['assets']],
            )
        )
        return results

    def list_latest_release_assets(self, name_pattern,
                                   content_type="application/octet-stream"):
        """Get a list of matching assets from a release.

        Args:
            name_pattern (str): Regex string to find the correct asset
                in the release. Leave blank to not download any assets
                (See return dict's 'assets' list to get
                'name' and 'content_type' of each asset).
            content_type (str, optional): Only allow this content type
                (May prevent mistakenly downloading the wrong asset).
                Leave blank to allow any. Ignored if no name_pattern.
                Defaults to "application/octet-stream".

        Raises:
            ValueError: _description_

        Returns:
            _type_: _description_
        """
        results = {}
        if self._latest_release_meta is None:
            release_results = self.refresh_latest_release()
            error = release_results.get('error')
            if error:
                results.update(release_results)
                return results

        assets = self._latest_release_meta.get('assets')
        if not assets:
            results['error'] = \
                "No 'assets' in {}".format(self._latest_releas_meta_src)
            return results
        if not name_pattern:
            results['assets'] = assets
            return results
        results['assets'] = []
        for asset in assets:
            # Examples: "yt-dlp", "yt-dlp.exe", "yt-dlp.tar.gz", "yt-dlp_linux",
            #   "yt-dlp_linux_aarch64", "yt-dlp_linux_armv7l", "yt-dlp_macos",
            #   "yt-dlp_macos.zip", "yt-dlp_macos_legacy", "yt-dlp_min.exe",
            #   "yt-dlp_win.zip", "yt-dlp_x86.exe", "_update_spec"
            asset_name = asset.get('name')
            if not asset_name:
                print("Warning: Unnamed asset listed: {}"
                      .format(json.dumps(asset, indent=2)))
                continue
            if name_pattern and (asset_name != name_pattern):
                continue
            browser_download_url = asset.get('browser_download_url')
            if not name_pattern:
                results['assets'].append(asset)
                continue
            if ((not asset.get('content_type'))
                    or (asset.get('content_type') != content_type)):
                raise ValueError(
                    "Content type of {}'s url={} is marked as {}"
                    " but {} was expected."
                    .format(asset_name, browser_download_url,
                            asset.get('content_type'), content_type)
                )
            results['assets'].append(asset)
        return results


def main():
    parser = argparse.ArgumentParser(
        description='Download a GitHub release asset.'
    )

    # Optional arguments
    parser.add_argument(
        '-O', '--output-file', type=str,
        help='Where to save (defaults to asset_name in current directory)'
    )

    # Positional arguments
    parser.add_argument(
        'account', type=str,
        help='The GitHub user or organization'
    )
    parser.add_argument(
        'project', type=str,
        help='The GitHub project name'
    )
    parser.add_argument(
        'asset_name', type=str,
        help=(
            'The asset name as listed on the release page, either generated by'
            ' GitHub from a tag such as "v1.0.tar.gz", or a custom asset'
            ' (uploaded by a maintainer or created by repo scripts) such as'
            ' "HashMan_v1.0_win32.zip".'
        )
    )

    # Parse the arguments
    args = parser.parse_args()

    # Print the values
    if args.output_file:
        dst_path = args.output_file
    else:
        dst_path = os.path.join(sysdirs['LOCAL_BIN'],
                                args.asset_name)
    tmp_path = dst_path + '.tmp'
    print("Account:", args.account)
    print("Project:", args.project)
    print("Asset Name:", args.asset_name)
    repo = RepoState(args.account, args.project)
    results = repo.download_one_asset(
        args.asset_name,
        destination_name=tmp_path,
    )
    error = results.get('error')
    if error:
        print("Downloading {} failed: {}"
              .format(results.get('url'), error))
        return 1
    path = results.get('path')
    if not path or not path.strip():
        raise NotImplementedError("No path and no error.")
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IXUSR)
    # ^ same as stat.S_IEXEC: "Unix V7 synonym for S_IXUSR."
    dst_parent = os.path.dirname(dst_path)
    if not os.path.isdir(dst_parent):
        os.makedirs(dst_parent)
    shutil.move(path, dst_path)
    print("dst_path=\"%s\"" % dst_path)
    return 0



if __name__ == "__main__":
    sys.exit(main())
