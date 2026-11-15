"""OpenAI-compatible AI chat dialog for Gold & Diamond Browser."""
from __future__ import annotations

import json
import os
from urllib.parse import urlparse

from PySide6.QtCore import QByteArray, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextBrowser,
    QVBoxLayout,
)


class AIAssistantDialog(QDialog):
    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Gold & Diamond AI")
        self.resize(760, 620)
        self.messages = [{
            "role": "system",
            "content": "You are Gold & Diamond AI, a helpful assistant inside Gold & Diamond Browser. Be clear, accurate, and concise.",
        }]
        self.network = QNetworkAccessManager(self)
        self.network.finished.connect(self._response_received)

        layout = QVBoxLayout(self)
        heading = QLabel("◆  GOLD & DIAMOND AI")
        heading.setStyleSheet("font-size:16pt;font-weight:700;padding:8px;color:#e5b85c")
        layout.addWidget(heading)
        self.transcript = QTextBrowser()
        self.transcript.setOpenExternalLinks(True)
        self.transcript.setPlaceholderText("Ask a question to get started.")
        layout.addWidget(self.transcript, 1)
        row = QHBoxLayout()
        self.prompt = QLineEdit()
        self.prompt.setPlaceholderText("Ask Gold & Diamond AI…")
        self.prompt.returnPressed.connect(self.send_message)
        self.send_button = QPushButton("Ask")
        self.send_button.clicked.connect(self.send_message)
        row.addWidget(self.prompt, 1)
        row.addWidget(self.send_button)
        layout.addLayout(row)
        self.status = QLabel("AI provider is configured in Settings → AI assistant.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self._append("Gold & Diamond AI", "Hello! Ask me something. Configure an API key using GDB_AI_API_KEY.")

    def _append(self, speaker: str, text: str):
        safe_speaker = speaker.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        safe_text = (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                     .replace("\n", "<br>"))
        self.transcript.append(
            f'<p><b style="color:#d8b35d">{safe_speaker}</b><br>{safe_text}</p>'
        )

    def send_message(self):
        prompt = self.prompt.text().strip()
        if not prompt:
            return
        api_key = os.environ.get("GDB_AI_API_KEY", "").strip()
        if not api_key:
            self.status.setText(
                "Missing API key. Set GDB_AI_API_KEY in your operating system environment, then restart the browser."
            )
            return
        base_url = str(self.settings.get("ai_base_url", "https://api.openai.com/v1")).rstrip("/")
        parsed = urlparse(base_url)
        if parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1"}:
            self.status.setText("For safety, remote AI providers must use HTTPS.")
            return
        model = str(self.settings.get("ai_model", "gpt-4o-mini")).strip()
        self.prompt.clear()
        self._append("You", prompt)
        self.messages.append({"role": "user", "content": prompt})
        self.send_button.setEnabled(False)
        self.status.setText("Gold & Diamond AI is thinking…")

        request = QNetworkRequest(QUrl(base_url + "/chat/completions"))
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        request.setRawHeader(b"Authorization", QByteArray(b"Bearer " + api_key.encode("utf-8")))
        payload = {
            "model": model,
            "messages": self.messages,
            "temperature": 0.7,
        }
        self.network.post(request, QByteArray(json.dumps(payload).encode("utf-8")))

    def _response_received(self, reply: QNetworkReply):
        self.send_button.setEnabled(True)
        body = bytes(reply.readAll()).decode("utf-8", errors="replace")
        if reply.error() != QNetworkReply.NetworkError.NoError:
            self.status.setText(f"AI request failed: {reply.errorString()}")
            reply.deleteLater()
            return
        try:
            data = json.loads(body)
            answer = data["choices"][0]["message"]["content"]
            if not isinstance(answer, str):
                raise ValueError("The provider returned an unsupported response.")
        except (ValueError, KeyError, IndexError, TypeError, json.JSONDecodeError):
            self.status.setText("The AI provider returned an unreadable response.")
            reply.deleteLater()
            return
        self.messages.append({"role": "assistant", "content": answer})
        self._append("Gold & Diamond AI", answer)
        self.status.setText("Ready")
        reply.deleteLater()
