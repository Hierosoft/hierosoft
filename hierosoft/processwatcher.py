# -*- coding: utf-8 -*-
import six
import subprocess
import sys
import threading
from queue import Queue, Empty

from hierosoft.morelogging import formatted_ex


class ProcessInfo():
    def __init__(self, launcher_cmd, **kwargs):
        self._err_bytes = None  # type: str|None
        self.ex = None  # type: Exception|None
        self.code = None  # type: int|None
        self.launcher_cmd = launcher_cmd
        # kwargs['stdout'] = subprocess.PIPE
        # kwargs['stderr'] = subprocess.STDOUT  # subprocess.PIPE
        # ^ NOTE: subprocess.STDOUT forces correct order
        #   but prevents distinguishing
        self.kwargs = kwargs
        assert launcher_cmd, "launcher_cmd not set"
        assert isinstance(launcher_cmd, (list, tuple))


class ProcessWatcher(ProcessInfo):
    def __init__(self, launcher_cmd, **kwargs):
        super().__init__(launcher_cmd, **kwargs)
        # IMPORTANT: Do NOT merge stderr → stdout if you want them separate!
        # Remove or comment out this line:
        # self.kwargs['stderr'] = subprocess.STDOUT
        self._err_bytes = None  # type: bytearray|None
        self._out_bytes = None  # type: bytearray|None
        self.code = None
        for part in launcher_cmd:
            assert isinstance(part, str), f"non-str in {launcher_cmd}"

    @property
    def error(self):
        if self._err_bytes is None:
            return None
        return six.ensure_str(self._err_bytes)

    @property
    def output(self):
        if self._out_bytes is None:
            return None
        return six.ensure_str(self._out_bytes)

    def _start_sync(self):
        self.code = None
        self._out_bytes = bytearray()
        self._err_bytes = bytearray()
        self.proc = subprocess.Popen(
            self.launcher_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,  # separate!
            **self.kwargs,
        )

        # Queues to collect output safely from threads
        stdout_queue = Queue()
        stderr_queue = Queue()

        def reader(pipe, queue):
            """Thread target: read lines from pipe and put them in queue"""
            try:
                for line in iter(pipe.readline, b''):
                    queue.put(line)
            finally:
                queue.put(None)  # sentinel to signal EOF

        # Start reader threads
        t_out = threading.Thread(target=reader, args=(self.proc.stdout, stdout_queue), daemon=True)
        t_err = threading.Thread(target=reader, args=(self.proc.stderr, stderr_queue), daemon=True)
        t_out.start()
        t_err.start()
        # We need to drain both queues in the main thread to avoid blocking
        # Use a simple non-blocking poll loop
        while self.proc.poll() is None or not stdout_queue.empty() or not stderr_queue.empty():
            # Try to get from stdout
            try:
                line = stdout_queue.get_nowait()
                if line is None:
                    # EOF from stdout
                    pass
                else:
                    sys.stdout.buffer.write(line)
                    sys.stdout.flush()
                    self._out_bytes += line
                    # Optionally store: self.outputs.append(line.decode(errors='replace'))
            except Empty:
                pass

            # Try to get from stderr
            try:
                line = stderr_queue.get_nowait()
                if line is None:
                    # EOF from stderr
                    pass
                else:
                    sys.stderr.buffer.write(line)
                    sys.stderr.flush()
                    self._err_bytes += line
                    # Optionally store: self.errors.append(line.decode(errors='replace'))
            except Empty:
                pass

            # Small sleep to avoid CPU spin
            # (you can remove/adjust this if you want lower latency)
            # time.sleep(0.01)

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
            except Empty:
                break

        # Wait for threads to finish (they should already be done)
        t_out.join()
        t_err.join()

        # Close pipes
        self.proc.stdout.close()
        self.proc.stderr.close()

        # Get return code
        self.code = self.proc.returncode

        # Your existing error logic (last non-empty stderr line, etc.)
        if self.code != 0:
            # ... your reversed(errors) logic ...
            pass

    def start_sync(self):
        try:
            self._start_sync()
        except Exception as ex:
            self.ex = ex
            self._err_bytes = formatted_ex(ex)  # assuming you have this
            raise

    def start(self):
        launch_t = threading.Thread(target=self.start_sync, daemon=True)
        launch_t.start()
        return launch_t
