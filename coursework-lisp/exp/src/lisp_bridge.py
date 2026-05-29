from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger


class LispBridgeError(RuntimeError):
    pass


class LispBridge:
    def __init__(self, sbcl_path: str, main_lisp: Path) -> None:
        self.sbcl_path = sbcl_path
        self.main_lisp = main_lisp
        self._lock = threading.Lock()
        self._proc: Optional[subprocess.Popen[str]] = None
        self._start()

    def _start(self) -> None:
        if not shutil.which(self.sbcl_path):
            raise LispBridgeError(f"SBCL не найден: {self.sbcl_path}")
        if not self.main_lisp.exists():
            raise LispBridgeError(f"Не найден: {self.main_lisp}")

        self._proc = subprocess.Popen(
            [self.sbcl_path, "--noinform", "--disable-debugger", "--load", str(self.main_lisp)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        if self._read_json().get("status") != "ok":
            raise LispBridgeError("Lisp не стартовал")

        init = self.call("init")
        logger.info("Lisp: {} книг", init.get("frames_count"))

    def _read_json(self) -> Dict[str, Any]:
        assert self._proc and self._proc.stdout
        while True:
            line = self._proc.stdout.readline()
            if not line:
                stderr = self._proc.stderr.read() if self._proc.stderr else ""
                raise LispBridgeError(f"Lisp завершился. stderr={stderr}")
            line = line.strip()
            if line.startswith("{"):
                return json.loads(line)

    def call(self, cmd: str, *parts: str) -> Dict[str, Any]:
        line = cmd if not parts else "|".join((cmd, *parts))
        with self._lock:
            assert self._proc and self._proc.stdin
            self._proc.stdin.write(line + "\n")
            self._proc.stdin.flush()
            response = self._read_json()
        if response.get("status") == "error":
            raise LispBridgeError(response.get("message", "Lisp error"))
        return response

    def close(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            self._proc.wait(timeout=5)


def create_bridge() -> LispBridge:
    root = Path(__file__).resolve().parents[2]
    return LispBridge(os.getenv("SBCL_PATH", "sbcl"), root / "lisp" / "src" / "main.lisp")
