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
    """Мост к ядру экспертной системы на Common Lisp (SBCL)."""

    def __init__(self, sbcl_path: str, main_lisp: Path) -> None:
        self.sbcl_path = sbcl_path
        self.main_lisp = main_lisp
        self._lock = threading.Lock()
        self._proc: Optional[subprocess.Popen[str]] = None
        self._start()

    def _start(self) -> None:
        if not shutil.which(self.sbcl_path):
            raise LispBridgeError(
                f"SBCL не найден: {self.sbcl_path}. "
                "Установите SBCL или задайте переменную SBCL_PATH."
            )
        if not self.main_lisp.exists():
            raise LispBridgeError(f"Не найден файл Lisp: {self.main_lisp}")

        cmd = [
            self.sbcl_path,
            "--noinform",
            "--disable-debugger",
            "--load",
            str(self.main_lisp),
        ]
        logger.info("Запуск Lisp-ядра: {}", " ".join(cmd))
        self._proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        ready = self._read_json()
        if ready.get("status") != "ok":
            raise LispBridgeError(f"Lisp-ядро не стартовало: {ready}")

        init_resp = self.call("init")
        if init_resp.get("status") != "ok":
            raise LispBridgeError(f"Ошибка инициализации Lisp: {init_resp}")

        logger.info(
            "Lisp-ядро инициализировано: {} книг, {} правил",
            init_resp.get("frames_count"),
            init_resp.get("rules_count"),
        )

    def _read_line(self) -> str:
        assert self._proc and self._proc.stdout
        line = self._proc.stdout.readline()
        if not line:
            stderr = ""
            if self._proc.stderr:
                stderr = self._proc.stderr.read()
            raise LispBridgeError(f"Lisp-процесс завершился неожиданно. stderr={stderr}")
        return line.strip()

    def _read_json(self) -> Dict[str, Any]:
        while True:
            line = self._read_line()
            if line.startswith("{"):
                return json.loads(line)
            logger.debug("Пропуск строки SBCL: {}", line[:120])

    def call(self, cmd: str, **payload: Any) -> Dict[str, Any]:
        request = {"cmd": cmd, **payload}
        line = json.dumps(request, ensure_ascii=False)

        with self._lock:
            assert self._proc and self._proc.stdin
            self._proc.stdin.write(line + "\n")
            self._proc.stdin.flush()
            response = self._read_json()

        if response.get("status") == "error":
            raise LispBridgeError(response.get("message", "Unknown Lisp error"))
        return response

    def close(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            self._proc.wait(timeout=5)


def create_bridge() -> LispBridge:
    project_root = Path(__file__).resolve().parents[2]
    lisp_main = project_root / "lisp" / "src" / "main.lisp"
    sbcl_path = os.getenv("SBCL_PATH", "sbcl")
    return LispBridge(sbcl_path=sbcl_path, main_lisp=lisp_main)
