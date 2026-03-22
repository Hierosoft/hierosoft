# -*- coding: utf-8 -*-
# https://grok.com/share/c2hhcmQtMg_0a054d0a-2bdf-4e7e-9c27-860e1bdc09d5
import six
import subprocess
import sys
import threading
import time

from queue import Queue, Empty

from hierosoft.morelogging import formatted_ex


class ProcessInfo:
    def __init__(self, launcher_cmd, **kwargs):
        self._err_bytes = None  # type: bytearray|None
        self.ex = None  # type: Exception|None
        self.code = None  # type: int|None
        self.launcher_cmd = launcher_cmd
        kwargs['stdout'] = subprocess.PIPE
        kwargs['stderr'] = subprocess.PIPE
        # kwargs['stderr'] = subprocess.STDOUT  # subprocess.PIPE
        # ^ NOTE: subprocess.STDOUT forces correct order
        #   but prevents distinguishing
        self.kwargs = kwargs
        assert launcher_cmd, "launcher_cmd not set"
        assert isinstance(launcher_cmd, (list, tuple))


class ProcessWatcher(ProcessInfo):
    def __init__(self, launcher_cmd, **kwargs):
        # super().__init__(launcher_cmd, **kwargs)
        ProcessInfo.__init__(self, launcher_cmd, **kwargs)
        self._err_bytes = None  # type: bytearray|None
        self._out_bytes = None  # type: bytearray|None
        self.code = None
        for part in launcher_cmd:
            assert isinstance(part, str), "non-str in {}".format(launcher_cmd)

    @property
    def error(self):
        if ((self._err_bytes is None) or (not self._err_bytes)
                or (not self._err_bytes.strip())):
            return None
        return six.ensure_str(self._err_bytes)

    @property
    def output(self):
        if ((self._out_bytes is None) or (not self._out_bytes)
                or (not self._out_bytes.strip())):
            return None
        return six.ensure_str(self._out_bytes)

    def _start_sync(self):
        self.code = None
        self._out_bytes = bytearray()
        self._err_bytes = bytearray()

        self.proc = subprocess.Popen(
            self.launcher_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,  # keep separate
            **self.kwargs,
        )

        # Queues to collect output safely from threads
        stdout_queue = Queue()
        stderr_queue = Queue()

        def reader(pipe, queue):
            """Read lines from pipe and put them (as bytes) into queue"""
            try:
                for line in iter(pipe.readline, b''):
                    if line:  # avoid empty chunks (no strip, maybe incomplete)
                        queue.put(line)
            finally:
                queue.put(None)  # sentinel to signal EOF

        # Start reader threads
        t_out = threading.Thread(
            target=reader,
            args=(self.proc.stdout, stdout_queue),
            daemon=True,
        )
        t_err = threading.Thread(
            target=reader,
            args=(self.proc.stderr, stderr_queue),
            daemon=True,
        )
        t_out.start()
        t_err.start()
        # We need to drain both queues in the main thread to avoid blocking
        # Use a simple non-blocking poll loop
        last_nonempty_err_line = None
        while ((self.proc.poll() is None)
               or (not stdout_queue.empty()) or (not stderr_queue.empty())):
            # Drain stdout
            try:
                line = stdout_queue.get_nowait()
                if line is None:
                    # EOF from stdout
                    pass
                else:
                    sys.stdout.buffer.write(line)
                    sys.stdout.flush()
                    self._out_bytes += line
                    # Optionally store: self.outputs.append(
                    #     line.decode(errors='replace'))
            except Empty:
                pass

            # Drain stderr
            try:
                line = stderr_queue.get_nowait()
                if line is None:
                    # EOF from stderr
                    pass
                else:
                    sys.stderr.buffer.write(line)
                    sys.stderr.flush()
                    self._err_bytes += line

                    # Track last non-empty line for error reporting
                    decoded = line.decode('utf-8',
                                          errors='replace').rstrip('\r\n')
                    if decoded.strip():
                        last_nonempty_err_line = decoded
            except Empty:
                pass

            # Small sleep to avoid CPU spin
            # (you can remove/adjust this if you want lower latency)
            time.sleep(0.01)

        # Final drain in case anything is left
        while True:
            try:
                line = stdout_queue.get_nowait()
                if line is not None:
                    sys.stdout.buffer.write(line)
                    sys.stdout.flush()
                    self._out_bytes += line
            except Empty:
                break

        while True:
            try:
                line = stderr_queue.get_nowait()
                if line is not None:
                    sys.stderr.buffer.write(line)
                    sys.stderr.flush()
                    self._err_bytes += line

                    decoded = line.decode('utf-8',
                                          errors='replace').rstrip('\r\n')
                    if decoded.strip():
                        last_nonempty_err_line = decoded
            except Empty:
                break

        # Wait for threads to finish (they should already be done)
        t_out.join()
        t_err.join()

        assert self.proc.stdout is not None
        assert self.proc.stderr is not None
        self.proc.stdout.close()
        self.proc.stderr.close()

        self.code = self.proc.returncode

        # Apply your original error logic
        if self.code != 0:
            if last_nonempty_err_line:
                self._err_bytes = bytearray(last_nonempty_err_line.encode(
                    'utf-8', errors='replace'))
                self.code = -1
            else:
                self._err_bytes = bytearray("return code {}"
                                            .format(self.code)
                                            .encode('utf-8'))

    def start_sync(self):
        try:
            self._start_sync()
        except Exception as ex:
            self.ex = ex
            error = formatted_ex(ex)
            self._err_bytes = \
                bytearray(error.encode('utf-8', errors='replace'))
            raise

    def start(self):
        launch_t = threading.Thread(target=self.start_sync, daemon=True)
        launch_t.start()
        return launch_t
