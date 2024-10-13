from __future__ import print_function
import glob
import os
import psutil
import shutil
import subprocess
import sys

from pathlib import Path

enable_tk = False

try:
    if sys.version_info.major >= 3:
        from tkinter import messagebox
    else:
        import tkMessageBox as messagebox
    enable_tk = True
except ImportError:
    print("Warning: tk could not be imported,"
          " so this program will try to use xmessage."
          " Try installing python3-tkinter to avoid this.",
          file=sys.stderr)
    pass

if sys.version_info.major >= 3:
    from shlex import join as shlex_join
else:
    def shlex_join(parts):
        result = ""
        space = ""
        for part in parts:
            if " " in part:
                result += space + "'" + part.replace("'", "\\'") + "'"
            space = " "
        return result

ME = "ardour-without-nextcloud"
MY_PIDS_DIR = os.path.join(
    str(Path.home()),
    ".var/run",
    ME
)

MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(MODULE_DIR)
if __name__ == "__main__":
    sys.path.insert(0, REPO_DIR)

from hierosoft.programinfo import (
    ProgramInfo,
)



def clean_file_name(name):
    """Replace all non-alphanumeric characters with underscores."""
    return ''.join(c if c.isalnum() else '_' for c in name)


class ProcessWrapper:
    """A wrapper to manage the lifecycle of a process
    Ensures that any previously running instances are correctly handled.

    Attributes:
        ardour_path (str): The default path to the Ardour executable.
        my_pid_path (str): The path to the current script's PID file.
        yad_pid_path (str): The path to the YAD tray icon's PID file.
        nextcloud_pid_path (str): The path to the Nextcloud PID file.
            (not critical, just proves whether this script started
            Nextcloud or not. This script doesn't terminate it
            forcefully, but instead calls "nextcloud --quit".

    Arguments:
        target (str): The path to the target executable.
        find_bin_pattern (str): The pattern to match process names
            (default: None). If None, it defaults to the basename
            of `target`.
        pid_file_name (str): The name for the PID file (default: None).
            If None, it defaults to `clean_file_name(find_bin_pattern)`.
    """

    # ardour_path = "/opt/Ardour-8.6.0/bin/ardour8"
    ardour_path = "/opt/Ardour-*/bin/ardour*"
    my_pid_path = os.path.join(MY_PIDS_DIR, "bash.pid")
    yad_pid_path = os.path.join(MY_PIDS_DIR, "yad.pid")
    nextcloud_pid_path = os.path.join(MY_PIDS_DIR, "nextcloud.pid")
    try_pause_icons = [
        "/usr/share/doc/nextcloud-desktop/html/_images/icon-paused.png",
        "/usr/share/icons/hicolor/48x48/apps/Nextcloud_warn.png",
        "/usr/share/icons/Papirus-Light/24x24/panel/pcloud-pause.svg",
        "/usr/share/icons/hicolor/32x32/status/laptopconnected.svg"
    ]
    yad_path = "yad"

    def __init__(self, target, find_bin_pattern=None, pid_file_name=None):
        self.target = target if target else self.ardour_path
        if "*" in self.target:
            programs = []
            highest_i = -1
            highest_version = (0, 0, 0)
            for path in list(sorted(glob.glob(self.target))):
                prog = ProgramInfo()
                prog.set_path(path)
                if (prog.version_tuple()
                        and (prog.version_tuple() > highest_version)):
                    highest_i = len(programs)
                    highest_version = prog.version_tuple()
                    # Keep the "highest" version, such as if the file
                    #   has 8 and the directory has 8.6.0, keep
                    #   8.6.0 since it has the most info.
                programs.append(prog)
            if len(programs) == 1:
                self.target = programs[0].path
            elif highest_i > -1:
                self.target = programs[highest_i].path
            else:
                self.target = programs[-1].path
        self.find_bin_pattern = (
            find_bin_pattern or os.path.basename(self.target))
        self.target_pid_path = (
            pid_file_name or clean_file_name(self.find_bin_pattern))
        self.bin_name = os.path.basename(self.target)
        self.my_pid = os.getpid()
        self.pause_icon = None
        self.enable_yad = True

    def run(self):
        """
        Executes the main logic to check, clean, and manage running processes.

        Returns:
            int: The exit code. 0 if successful, otherwise a non-zero value
            indicating an error or issue.
        """
        other_pids = []
        other_names = []
        other_pid_paths = []

        os.makedirs(MY_PIDS_DIR, exist_ok=True)

        if self.target_pid_path:
            target_pid_path = self.target_pid_path
        else:
            target_pid_path = os.path.join(MY_PIDS_DIR,
                                           "{0}.pid".format(self.bin_name))

        # Check and clean old PID files
        stated_pids = []
        for try_pid_path in [self.my_pid_path, target_pid_path,
                             self.yad_pid_path]:
            if os.path.isfile(try_pid_path):
                try:
                    with open(try_pid_path, 'r') as f:
                        try_pid = int(f.read().strip())
                    if psutil.pid_exists(try_pid):
                        print("Error: {0} is running ({1}).".format(
                            try_pid, try_pid_path))
                        stated_pids.append(try_pid)
                    else:
                        print("Warning: No PID {0}. Removing old {1}".format(
                            try_pid, try_pid_path))
                        os.remove(try_pid_path)
                except ValueError:
                    print("Invalid PID found in {0}. Removing file.".format(
                        try_pid_path))
                    os.remove(try_pid_path)

        # Find and handle other running processes
        got_pids = self.find_running_processes(self.find_bin_pattern)

        if got_pids:
            for got_pid in got_pids:
                if got_pid in stated_pids:
                    # Already recorded above
                    continue
                other_pids.append(got_pid)
                other_names.append("{} (not started by {})"
                                   .format(self.find_bin_pattern, ME))
            # if not os.path.isfile(target_pid_path):

        delete_instruction = ""
        if len(other_pid_paths) > 0:
            delete_instruction = "delete {}\nand ".format(
                " ".join(other_pid_paths))
        if os.path.isfile(self.my_pid_path):
            delete_instruction = ""
            with open(self.my_pid_path, 'r') as f:
                other_my_pid = int(f.read().strip())
            other_pids.append(other_my_pid)
            other_names.append(ME)
            other_pid_paths.append(self.my_pid_path)

        if os.path.isfile(target_pid_path):
            with open(target_pid_path, 'r') as f:
                other_my_pid = int(f.read().strip())
            other_pids.append(other_my_pid)
            other_names.append(self.bin_name)
            other_pid_paths.append(target_pid_path)

        if os.path.isfile(self.yad_pid_path):
            with open(self.yad_pid_path, 'r') as f:
                other_my_pid = int(f.read().strip())
            other_pids.append(other_my_pid)
            other_names.append("yad")
            other_pid_paths.append(self.yad_pid_path)
        delete_msg = ""
        if len(other_pid_paths) > 0:
            pass
            # delete_msg = " and delete {}".format(other_pid_paths)
            # ^ Deleting is invalid since invalid ones *not representing
            #   actual processes* were already deleted further up.
        plural = True if (len(other_names) > 1) else False
        pid_noun = "pids" if plural else "pid"
        program_noun = "programs" if plural else "program"
        verb = "are" if plural else "is"

        opener = "If"
        if os.path.isfile(self.my_pid_path):
            opener = "Switch to {0} to use it,\nor if".format(self.bin_name)
        if os.path.isfile(target_pid_path):
            if opener == "If":
                opener = "Close {0} & reopen it with {1},\nor if".format(
                    self.bin_name, ME)

        # if opener == "If":
        #     opener += " {}".format(verb)

        # Error handling for running processes
        error = ""
        if other_pids:
            error = (
                "{} {} ({} {}) already running.\n\n{} "
                " you launched the program with"
                " the regular shortcut icon,\n{}close the {}"
                "{} and try this special icon again.".format(
                    ", ".join(other_names),  # 1st
                    verb,  # 2nd
                    pid_noun,  # 3rd
                    ", ".join(map(str, other_pids)),  # 4th
                    opener,  # 5th
                    # ME,  # 6th
                    delete_instruction,
                    program_noun,
                    delete_msg,
                )
            )

        if error:
            print(error)
            if enable_tk:
                # error = error.replace("\n", " ").replace("  ", " ")
                messagebox.showinfo(ME, error)
            else:
                subprocess.run(["xmessage", error])
            # os.remove(self.my_pid_path)  # not yet: created below
            return 3

        # Save the current PID
        with open(self.my_pid_path, 'w') as f:
            f.write(str(self.my_pid))

        msg = ("yad ({0}): {1} ({2}) stopped Nextcloud until {3} is closed."
               .format(self.yad_pid_path, ME, self.my_pid, self.bin_name))
        print(msg)

        if not self.pause_icon:
            # Determine PAUSE_ICON
            self.pause_icon = ProcessWrapper.try_pause_icons[0]
            for icon_path in ProcessWrapper.try_pause_icons:
                if os.path.isfile(icon_path):
                    self.pause_icon = icon_path
                    break

        # Stop Nextcloud
        subprocess.run(["nextcloud", "--quit"])
        if os.path.isfile(self.nextcloud_pid_path):
            os.remove(self.nextcloud_pid_path)

        # Start YAD tray icon
        self.enable_yad = True
        yad_proc = None
        yad_pid = None
        try:
            yad_proc = subprocess.Popen([
                ProcessWrapper.yad_path,
                "--notification",
                "--image",
                self.pause_icon,
                "--text",
                msg,
            ])
            yad_pid = yad_proc.pid
        except FileNotFoundError as ex:
            print("{}: {}".format(type(ex).__name__, ex))
            self.enable_yad = False

        if yad_pid:
            with open(self.yad_pid_path, 'w') as f:
                f.write(str(yad_pid))

        # Run the target program
        cmd_parts = [self.target] + sys.argv[1:]
        target_proc = subprocess.Popen(
            cmd_parts,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        target_pid = target_proc.pid
        with open(target_pid_path, 'w') as f:
            f.write(str(target_pid))

        # Wait for the target program to exit
        # target_proc.wait()
        out, err = target_proc.communicate()
        if sys.version_info.major >= 3:
            out = out.decode()
            err = err.decode()
        return_code = target_proc.returncode
        if return_code != 0:
            error = "%s failed with error" % shlex_join(cmd_parts)
            if out:
                error += "\n" + out
            if err:
                error += "\n" + err
            messagebox.showerror("ProcessWrapper.", error)
        os.remove(target_pid_path)

        # Restart Nextcloud
        nextcloud_proc = subprocess.Popen(["nextcloud", "--background"])
        if nextcloud_proc.returncode != 0:
            with open(self.nextcloud_pid_path + ".error", 'w') as f:
                f.write("'nextcloud --background &' returned error code {0}"
                        .format(nextcloud_proc.returncode))

        # Cleanup YAD
        if yad_proc:
            yad_proc.terminate()
            if yad_proc.returncode != 0:
                with open(self.yad_pid_path + ".error", 'w') as f:
                    f.write("'kill {0}' returned error code {1}".format(
                            yad_pid, yad_proc.returncode))

        # if self.enable_yad:
        if os.path.isfile(self.yad_pid_path):
            os.remove(self.yad_pid_path)

        os.remove(self.my_pid_path)  # un-mark self before *every* return
        return 0

    def find_running_processes(self, pattern):
        """
        Finds running processes that match the `pattern`.

        Returns:
            list: A list of PIDs matching the `pattern`.
        """
        found_processes = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if pattern.lower() in proc.info['name'].lower():
                    found_processes.append(proc.info['pid'])
                else:
                    print("{} is not like {}"
                          .format(proc.info['name'], pattern))
            except (psutil.NoSuchProcess, psutil.AccessDenied,
                    psutil.ZombieProcess):
                pass
        return found_processes


if __name__ == "__main__":
    print(
        "Nothing to do: You ran a module ({})."
        " See linux-preinstall/utilities/ardour-without-nextcloud.py"
        " for an example."
        .format(__file__))
    sys.exit(1)
