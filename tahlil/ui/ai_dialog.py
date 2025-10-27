from __future__ import annotations
from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QProcess, QProcessEnvironment, Qt, QSettings
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QListWidget,
    QMessageBox,
    QCheckBox,
    QSplitter,
    QWidget,
)


class AIDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("RAG Assistant")
        self.resize(800, 600)

        self._proc: Optional[QProcess] = None
        self._stdout_buf: str = ""
        self._extra: str = ""

        self.le_key = QLineEdit()
        self.le_key.setPlaceholderText("OPENROUTER_API_KEY (sk-or-...)")
        self.le_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.cb_remember = QCheckBox("Remember key (stored in plain settings)")

        self._load_key()

        key_row = QHBoxLayout()
        key_row.addWidget(QLabel("API Key:"))
        key_row.addWidget(self.le_key, 1)
        key_row.addWidget(self.cb_remember)

        self.txt_q = QPlainTextEdit()
        self.txt_q.setPlaceholderText("Ask your question...")

        self.btn_ask = QPushButton("Ask")
        self.btn_ask.clicked.connect(self._on_ask)

        self.txt_ans = QPlainTextEdit()
        self.txt_ans.setReadOnly(True)

        self.lst_src = QListWidget()

        split = QSplitter()
        wrap = QWidget()
        v = QVBoxLayout(wrap)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(QLabel("Answer"))
        v.addWidget(self.txt_ans, 1)
        split.addWidget(wrap)
        split.addWidget(self.lst_src)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)

        lay = QVBoxLayout(self)
        lay.addLayout(key_row)
        lay.addWidget(QLabel("Question"))
        lay.addWidget(self.txt_q, 1)
        lay.addWidget(self.btn_ask)
        lay.addWidget(split, 2)

    def _project_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def _venv_python(self) -> Path:
        root = self._project_root()
        return root / ".rag-venv" / "bin" / "python"

    def _rag_query_script(self) -> Path:
        root = self._project_root()
        return root / "agents" / "rag_agent" / "query.py"

    def _on_ask(self) -> None:
        if self._proc is not None and self._proc.state() != QProcess.ProcessState.NotRunning:
            return
        py = self._venv_python()
        script = self._rag_query_script()
        if not py.exists():
            QMessageBox.warning(self, "RAG", ".rag-venv not found. Set up the RAG agent first.")
            return
        if not script.exists():
            QMessageBox.warning(self, "RAG", "RAG query script not found.")
            return
        q = self.txt_q.toPlainText().strip()
        if not q:
            QMessageBox.information(self, "RAG", "Please enter a question.")
            return

        self._save_key_if_needed()

        self._stdout_buf = ""
        proc = QProcess(self)
        self._proc = proc
        env = QProcessEnvironment.systemEnvironment()
        key = self.le_key.text().strip()
        if key:
            env.insert("OPENROUTER_API_KEY", key)
        proc.setProcessEnvironment(env)
        proc.setProgram(str(py))
        args = [str(script), "-q", q]
        if self._extra.strip():
            args += ["--extra", self._extra]
        proc.setArguments(args)
        proc.readyReadStandardOutput.connect(self._on_stdout)
        proc.readyReadStandardError.connect(self._on_stderr)
        proc.finished.connect(self._on_finished)
        self.btn_ask.setEnabled(False)
        proc.start()

    def _on_stdout(self) -> None:
        if not self._proc:
            return
        data = bytes(self._proc.readAllStandardOutput()).decode(errors="ignore")
        self._stdout_buf += data

    def _on_stderr(self) -> None:
        if not self._proc:
            return
        bytes(self._proc.readAllStandardError()).decode(errors="ignore")

    def _on_finished(self, code: int, status: QProcess.ExitStatus) -> None:
        self.btn_ask.setEnabled(True)
        out = self._stdout_buf
        ans, srcs = self._parse_output(out)
        self.txt_ans.setPlainText(ans.strip())
        self.lst_src.clear()
        for s in srcs:
            self.lst_src.addItem(s)
        if code != 0 and not ans:
            QMessageBox.warning(self, "RAG", "Query process failed. Check your API key or network.")

    @staticmethod
    def _parse_output(text: str) -> tuple[str, list[str]]:
        ans = ""
        srcs: list[str] = []
        if "=== Answer ===" in text:
            part = text.split("=== Answer ===", 1)[1]
            if "=== Sources ===" in part:
                ans = part.split("=== Sources ===", 1)[0]
                src_block = part.split("=== Sources ===", 1)[1]
                for line in src_block.splitlines():
                    line = line.strip()
                    if line.startswith("["):
                        srcs.append(line)
            else:
                ans = part
        else:
            ans = text
        return ans.strip(), srcs

    def _load_key(self) -> None:
        s = QSettings()
        val = s.value("openrouter_api_key", "", str)
        if val:
            self.le_key.setText(val)
            self.cb_remember.setChecked(True)

    def _save_key_if_needed(self) -> None:
        s = QSettings()
        if self.cb_remember.isChecked():
            s.setValue("openrouter_api_key", self.le_key.text().strip())
        else:
            s.remove("openrouter_api_key")

    def set_extra_context(self, extra: str) -> None:
        self._extra = extra or ""
