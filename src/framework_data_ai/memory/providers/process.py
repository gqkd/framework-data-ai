"""Bounded subprocess transport, with logs kept out of structured results."""
from __future__ import annotations

import os
import selectors
import signal
import subprocess
import time

from ...workspace import MemoryInputError


def bounded_run(argv, *, env, timeout=45, limit=20_000_000):
    if os.name != "posix":
        raise MemoryInputError("isolated code observation currently requires Linux/WSL")
    process = subprocess.Popen(argv, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=True)
    output, log_size = bytearray(), 0
    deadline = time.monotonic() + timeout
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ, True)
            selector.register(process.stderr, selectors.EVENT_READ, False)
            while selector.get_map():
                if time.monotonic() >= deadline:
                    raise MemoryInputError("code provider or Git operation exceeded its timeout")
                for key, _ in selector.select(min(0.1, max(0, deadline - time.monotonic()))):
                    block = os.read(key.fd, 65536)
                    if not block:
                        selector.unregister(key.fileobj)
                    elif key.data:
                        output.extend(block)
                    else:
                        log_size += len(block)
                    if len(output) > limit or log_size > limit:
                        raise MemoryInputError("code provider or Git operation exceeded its output limit")
        return process.wait(timeout=max(0.01, deadline - time.monotonic())), bytes(output)
    except subprocess.TimeoutExpired as error:
        raise MemoryInputError("code provider or Git operation exceeded its timeout") from error
    finally:
        # Terminate descendants even if the group leader already exited.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        process.stdout.close()
        process.stderr.close()
