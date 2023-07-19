# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import shutil
import tempfile
import subprocess
import platform

from hierosoft import (
    echo0,
    SHORTCUT_EXT,
    CACHES,
)

# TODO: if shlex is used, do:
"""
if sys.version_info.major > 3 and sys.version_info.minor > 8:
    shlex_join = shlex.join
else:
    def shlex_join(parts):
        result = ""
        sep = ""
        for part in parts:
            result += sep
            sep = " "
            if (" " in part) or ('"' in part):
                result += '"%s"' % part.replace('"', '\\"')
            else:
                result += part
        return result
    shlex.join = shlex_join
"""

def make_shortcut(meta, program_name, mgr, push_label=echo0, uninstall=False):
    ret = True
    desktop_path = mgr.get_desktop_path()
    sc_ext = SHORTCUT_EXT
    bin_path = meta.get('installed_bin')
    action = "create"
    if uninstall:
        action = "uninstall"
    if not uninstall:
        if bin_path is None:
            msg = "installed_bin is missing from meta."
            push_label("{} shortcut failed since".format(action))
            push_label(msg)
            print(msg)
            return False
    print("* {} shortcut...".format(action))
    desktop_sc_name = program_name
    version = meta.get('version')
    sc_src_name = program_name
    if version is not None:
        desktop_sc_name += " " + version + " Nightly"
    sc_label_s = desktop_sc_name[0].upper() + desktop_sc_name[1:]
    if sc_ext != "desktop":
        # filename is visible if not "desktop" format, so capitalize
        desktop_sc_name = sc_label_s
    if len(sc_ext) > 0:
        desktop_sc_name += "." + sc_ext
        sc_src_name += "." + sc_ext
    else:
        print("WARNING: The shortcut extension is unknown for your"
              " platform.")
    desktop_sc_path = os.path.join(desktop_path, desktop_sc_name)

    user_downloads_path = mgr.get_downloads_path()
    bn_path = os.path.join(user_downloads_path, "blendernightly")
    # archives_path = os.path.join(bn_path, "archives")
    # if not os.path.isdir(archives_path):
        # print("  {}: ".format(action) + archives_path)
        # os.makedirs(archives_path)
    versions_path = os.path.join(bn_path, "versions")

    installed_path = os.path.join(versions_path, meta['id'])
    print("* id: {}".format(meta['id']))
    if sc_ext == "desktop":
        PREFIX = os.path.join(mgr.profile_path, ".local")
        BIN = os.path.join(PREFIX, "bin")
        sh_path = os.path.join(BIN, "blendernightly-logged.sh")
        logexec = bin_path
        # TODO: Prevent Blender startup crash:
        '''
        ERROR (gpu.shader): gpu_shader_2D_widget_base FragShader:
              |
           81 | layout(depth_any) out float gl_FragDepth;
              |         ^
              | Error: unrecognized layout identifier `depth_any'
        '''
        # on older video
        # cards not supporting OpenGL 4.2 as per
        # <https://developer.blender.org/T98708>:
        # logexec = "MESA_GL_VERSION_OVERRIDE=4.1" + logexec + ' > ' + CACHE + '/blender-`date "+%Y-%m-%d"`-gl4.1-error.log 2>&1'
        # MESA_GL_VERSION_OVERRIDE=4.1 /home/owner/Downloads/blendernightly/versions/3.2.0-stable+v32.e05e1e369187.x86_64-release/blender > /home/owner/.cache/blender-nightly/blender-`date "+%Y-%m-%d"`-gl4.1-error.log 2>&1
        CACHE = os.path.join(CACHES, "blender-nightly")
        if not os.path.isdir(CACHE):
            os.makedirs(CACHE)
        if bin_path is not None:
            logexec += ' > ' + CACHE + '/blender-`date "+%Y-%m-%d"`-error.log 2>&1'
        if not uninstall:
            with open(sh_path, 'w') as outs:
                outs.write("#!/bin/sh" + "\n")
                outs.write(logexec + "\n")
            os.chmod(sh_path, 0o755)
            print("* wrote {}".format(sh_path))
            if os.path.isfile(desktop_sc_path):
                print("* removing {}".format(desktop_sc_path))
                os.remove(desktop_sc_path)
            print("* writing {}...".format(desktop_sc_path))
            sc_src_path = os.path.join(installed_path, sc_src_name)
            if not os.path.isfile(sc_src_path):
                msg = sc_src_name + " is missing"
                push_label("ERROR: {} shortcut failed since"
                           "".format(action))
                push_label(msg)
                print(msg)
                return False
            with open(desktop_sc_path, 'w') as outs:
                with open(sc_src_path, "r") as ins:
                    for line_orig in ins:
                        line = line_orig.rstrip()
                        exec_flag = "Exec="
                        name_flag = "Name="
                        if line[:len(exec_flag)] == exec_flag:
                            exec_line = exec_flag + sh_path
                            print("  - {}".format(exec_line))
                            outs.write(exec_line + "\n")
                        elif line[:len(name_flag)] == name_flag:
                            name_line = name_flag + sc_label_s
                            print("  - {}".format(name_line))
                            outs.write(name_line + "\n")
                        else:
                            outs.write(line + "\n")
            try:
                # Keep the desktop shortcut and mark it executable.
                os.chmod(desktop_sc_path, 0o755)
                # ^ leading 0o denotes octal
            except Exception as ex:
                echo0("Warning: could not mark icon as executable ({})"
                      "".format(ex))
        else:
            pass
            # print("* {} is skipping shortcut writing".format(action))

        PREFIX = os.path.join(mgr.profile_path, ".local")
        SHARE = os.path.join(PREFIX, "share")
        applications_path = os.path.join(SHARE, "applications")
        if not uninstall:
            if not os.path.isdir(applications_path):
                os.makedirs(applications_path)
        sc_name = "org.blender.blender-nightly.desktop"
        sc_path = os.path.join(
            applications_path,
            sc_name
        )
        desktop_installer = "xdg-desktop-menu"
        u_cmd_parts = [desktop_installer, "uninstall", sc_path]
        if not uninstall:
            tmp_sc_dir_path = tempfile.mkdtemp()
            tmp_sc_path = os.path.join(tmp_sc_dir_path,
                                       sc_name)
            shutil.copy(desktop_sc_path, tmp_sc_path)
            print("* using {} for {}".format(desktop_sc_path, tmp_sc_path))
            # ^ XDG requires this naming.
        # "--novendor" can force it, but still not if there are spaces.

        # Always remove the old icons first, even if not uninstall:

        if os.path.isfile(desktop_sc_path):
            print("* removing {}...".format(desktop_sc_path))
            os.remove(desktop_sc_path)
        elif uninstall:
            print("* there is no {}...".format(desktop_sc_path))

        if os.path.isfile(sc_path):
            # print("* removing shortcut \"{}\"".format(sc_path))
            # os.remove(desktop_sc_path)
            print("* uninstalling shortcut \"{}\"".format(sc_path))
            subprocess.run(u_cmd_parts)
            # ^ Using only the name also works: sc_name])
            # ^ Using the XDG uninstall subcommand ensures that the
            #   icon in the OS application menu gets updated if the
            #   shortcut was there but different (such as with a
            #   different version number or otherwise different
            #   name).
        elif uninstall:
            print("* there is no {}...".format(sc_path))
        # else:
        #     print("* there's no {}...".format(sc_path))
        if not uninstall:
            sc_cmd_parts = [desktop_installer, "install", tmp_sc_path]
            install_proc = subprocess.run(sc_cmd_parts)
            inst_msg = "OK"
            os.remove(tmp_sc_path)
            if install_proc.returncode != 0:
                inst_msg = "FAILED"
                print("* {}...{}".format(" ".join(sc_cmd_parts),
                                         inst_msg))
                print("  - attempting to copy to {} manually..."
                      "".format(sc_path))
                shutil.copyfile(desktop_sc_path, sc_path)
            else:
                print("* {}...{}".format(" ".join(sc_cmd_parts),
                                         inst_msg))

    elif sc_ext == "bat":
        if not uninstall:
            outs = open(desktop_sc_path, 'w')
            outs.write('"' + bin_path + '"' + "\n")
            outs.close()
        else:
            if os.path.isfile(desktop_sc_path):
                print("* removing {}...".format(desktop_sc_path))
                os.remove(desktop_sc_path)
    elif sc_ext == "command":
        if not uninstall:
            outs = open(desktop_sc_path, 'w')
            outs.write('"' + bin_path + '"' + "\n")
            outs.close()
        else:
            if os.path.isfile(desktop_sc_path):
                print("* removing {}...".format(desktop_sc_path))
                os.remove(desktop_sc_path)
    else:
        msg = "unknown shortcut format " + sc_ext
        push_label("{} shortcut failed since".format(action))
        push_label(msg)
        print(msg)
    return ret
