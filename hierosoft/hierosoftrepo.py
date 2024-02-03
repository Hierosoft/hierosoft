import json
import os
import platform
# import sys

from collections import OrderedDict
from hierosoft.morelogging import (
    # is_enclosed,
    pformat,
    echo0,
)

MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(MODULE_DIR)
generated_name = "licenses.txt"
generated_path = os.path.join(REPO_DIR, generated_name)
if platform.system() == "Windows":
    HOME = os.environ['USERPROFILE']
else:
    HOME = os.environ['HOME']

licenses = [
    {
        'for': "Hierosoft Launcher",
        'path': os.path.join(REPO_DIR, "license.txt"),
    },
    {
        'for': "Forest Theme",
        'path': os.path.join(MODULE_DIR, "assets", "Forest-ttk-theme",
                             "LICENSE"),
    },
]


def relative_path(path):
    if path.startswith(REPO_DIR):
        return path[len(REPO_DIR)+1:]  # +1 to avoid leading slash (& stay rel)
    return path


FIRST = True


def append_to_license(title, path):
    prefix = "[append_to_license] "
    global FIRST
    mode = 'a'
    if FIRST:
        mode = 'w'
    mode_words = {
        'a': "appended",
        'w': "overwrote",
    }
    with open(generated_path, mode) as outs:
        if not FIRST:
            outs.write("\n")
            outs.write("\n")
        outs.write(title + "\n")
        outs.write(len(title)*"-" + "\n")  # Write an ASCII-art underline
        with open(path, 'r') as ins:
            for rawL in ins:
                line = rawL.rstrip("\r\n")  # Remove before consistent ones
                outs.write(line + '\n')
            print(prefix+"%s %s with %s" % (
                mode_words[mode],
                pformat(relative_path(path)),
                pformat(relative_path(generated_path)),
            ))
    FIRST = False


def generate_combined_license():
    global FIRST
    FIRST = True
    for meta in licenses:
        append_to_license(meta['for'], meta['path'])


def _pack_file(stream, name, path):
    stream.write(name+' = """')
    with open(path, 'r') as ins:
        data = ins.read()
        stream.write(data)
    print('"""', file=stream)
    print("packed text %s" % pformat(path))


def _pack_binary(stream, name, path):
    import base64
    import zlib
    opener = name+'_str = ('
    with open(path, 'rb') as ins:
        data = ins.read()
        big_string = base64.b64encode(zlib.compress(data)).decode('utf-8')
        print(opener, file=stream)
        del opener
        indent = "    "
        max_w = 79
        # Wrap long strings:
        while len(big_string) > 0:
            slack = len(indent) + 2  # +2 for quotes
            small_string = big_string
            if len(small_string) + slack > max_w:
                big_string = small_string[max_w-slack:]
                small_string = small_string[:max_w-slack]
            else:
                big_string = ""
            print(indent+'"%s"' % small_string, file=stream)
    print(')', file=stream)
    print("%s = zlib.decompress(base64.b64decode(\n"
          "    %s_str.encode('utf-8')\n))"
          % (name, name), file=stream)
    print("packed binary %s" % pformat(path))


def pack_text():
    prefix = "[pack_text] "
    ASSETS_DIR = os.path.join(MODULE_DIR, "assets")
    DATA_DIR = os.path.join(ASSETS_DIR, "data")
    pack_path = os.path.join(MODULE_DIR, "hierosoftpacked.py")
    CLOUD_DIR = os.path.join(HOME, "Nextcloud")
    CLOUD_PICTURES = os.path.join(CLOUD_DIR, "Pictures")
    transparent_path = os.path.join(CLOUD_PICTURES, "transparent.png")
    white_path = os.path.join(CLOUD_PICTURES, "white.png")
    LOGO_DIR = os.path.join(CLOUD_PICTURES, "Identity", "Hierosoft")
    hierosoft_16_path = os.path.join(LOGO_DIR, "logo-1.2.1-16px.png")
    SVG_DIR = os.path.join(LOGO_DIR,
                           "hierosoft-noscale-for_moresvg")
    svg_path = os.path.join(
        SVG_DIR,
        "logo-1.2.1-square-black-more_points-manually_combined_paths.svg"
    )
    if not os.path.isfile(svg_path):
        echo0("Warning: There is no %s. No packing will occur"
              " and %s will be left intact."
              % (pformat(svg_path), pformat(pack_path)))
        return
    json_path = os.path.join(DATA_DIR, "sources.json")
    with open(json_path, 'r') as ins:
        try:
            _ = json.load(ins)  # Ensure json is valid.
        except json.decoder.JSONDecodeError as ex:
            exStr = str(ex)
            lineI = exStr.find(": line ")
            error = exStr
            if lineI >= 0:
                # Make the error readable by the IDE (click to go to line)
                message = exStr[:lineI]
                position = exStr[lineI+1:]
                if "expecting value" in message.lower():
                    message += " (trailing comma is not allowed in JSON)"
                error = ('File "%s",%s: JSON SyntaxError: %s'
                         % (json_path, position, message))
            echo0(error)
            return 1
    if not os.path.isfile(pack_path):
        raise FileNotFoundError(
            "At least make a blank %s to ensure correct path is detected"
            % pack_path
        )
    pack_meta = OrderedDict(
        hierosoft_svg={
            "pre_line": "# hierosoft_svg is TM Hierosoft LLC, USA:",
            "path": svg_path,
        },
        sources_json={
            "pre_line": ("# this version's sources.json"
                         " (update is downloaded unless --offline):"),
            "path": json_path,
        },
    )
    me = os.path.basename(__file__)
    with open(pack_path, 'w') as stream:
        print("# -*- coding: utf-8 -*-", file=stream)
        print('"""', file=stream)
        print(
            ("Do not edit."
             " This file is generated by %s via prebuild." % me),
            file=stream
        )
        print("These files are packed for the binary version.", file=stream)
        print('"""', file=stream)
        print("import base64", file=stream)
        print("import zlib", file=stream)
        print("", file=stream)
        for key, info in pack_meta.items():
            print('', file=stream)
            pre_line = info.get("pre_line")
            if pre_line is not None:
                print(pre_line, file=stream)
            _pack_file(stream, key, info['path'])
            print(prefix+"packed %s into %s" % (
                pformat(relative_path(info['path'])),
                pformat(relative_path(pack_path))
            ))
        _pack_binary(stream, "transparent_png", transparent_path)
        _pack_binary(stream, "white_png", white_path)
        _pack_binary(stream, "hierosoft_16px_png", hierosoft_16_path)
