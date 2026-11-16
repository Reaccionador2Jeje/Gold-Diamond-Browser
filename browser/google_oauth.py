"""Official Google OAuth 2.0 authorization-code flow with PKCE for desktop clients.

Tokens are stored in the operating-system credential store through keyring.
No browser cookies are read, copied, exported, or injected.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import keyring
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QDialog, QLabel, QMessageBox, QPushButton, QVBoxLayout

SERVICE_NAME = "GoldDiamondBrowser.GoogleOAuth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
SCOPES = "openid email profile"


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


class _CallbackServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


class GoogleOAuthDialog(QDialog):
    """Connect a Google account using an installed-app OAuth client and PKCE."""

    def __init__(self, parent=None, profile_id: str = "default"):
        super().__init__(parent)
        self.profile_id = profile_id\n        self.setWindowTitle("Connect Google account")
        self.setMinimumWidth(430)
        self._server = None
        self._server_thread = None
        self._result = {}
        self._error = None
        self._state = secrets.token_urlsafe(32)
        self._verifier = _b64url(secrets.token_bytes(48))
        self._challenge = _b64url(hashlib.sha256(self._verifier.encode("ascii")).digest())

        layout = QVBoxLayout(self)
        self.info = QLabel(
            "Connect using Google's official sign-in page. Your password is entered "
            "only on Google. Gold & Diamond stores OAuth tokens in your operating "
            "system's credential store; it never imports browser cookies."
        )
        self.info.setWordWrap(True)
        layout.addWidget(self.info)
        self.connect_button = QPushButton("Continue with Google")
        self.connect_button.clicked.connect(self.start_authorization)
        layout.addWidget(self.connect_button)
        self.status = QLabel("A Google OAuth Desktop client ID is required.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.reject)
        layout.addWidget(self.close_button)

        self.poller = QTimer(self)
        self.poller.setInterval(250)
        self.poller.timeout.connect(self._poll_callback)

    def start_authorization(self):
        client_id = os.environ.get("GDB_GOOGLE_CLIENT_ID", "").strip()
        if not client_id:
            QMessageBox.information(
                self,
                "Google OAuth setup required",
                "Set GDB_GOOGLE_CLIENT_ID to the Client ID of a Google OAuth "
                "2.0 client configured as a Desktop app, then restart Gold & Diamond Browser.",
            )
            return

        dialog = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                parsed = urllib.parse.urlparse(self.path)
                query = urllib.parse.parse_qs(parsed.query)
                if parsed.path != "/oauth2/callback":
                    self.send_error(404)
                    return
                dialog._result = {
                    "state": query.get("state", [""])[0],
                    "code": query.get("code", [""])[0],
                    "error": query.get("error", [""])[0],
                }
                body = (
                    b"Authorization received. You can return to Gold & Diamond Browser."
                    if dialog._result.get("code")
                    else b"Authorization was not completed. Return to Gold & Diamond Browser."
                )
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):
                return

        try:
            self._server = _CallbackServer(("127.0.0.1", 0), Handler)
            port = self._server.server_address[1]
            self._server_thread = threading.Thread(
                target=self._server.serve_forever, daemon=True
            )
            self._server_thread.start()
        except OSError as exc:
            QMessageBox.warning(self, "OAuth callback", f"Could not start the local callback: {exc}")
            return

        self._client_id = client_id
        self._redirect_uri = f"http://127.0.0.1:{port}/oauth2/callback"
        params = {
            "client_id": client_id,
            "redirect_uri": self._redirect_uri,
            "response_type": "code",
            "scope": SCOPES,
            "state": self._state,
            "code_challenge": self._challenge,
            "code_challenge_method": "S256",
            "access_type": "offline",
            "prompt": "consent",
        }
        url = AUTH_URL + "?" + urllib.parse.urlencode(params)
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        if not QDesktopServices.openUrl(QUrl(url)):
            self._stop_server()
            QMessageBox.warning(self, "Google sign-in", "Could not open the system browser.")
            return
        self.connect_button.setEnabled(False)
        self.status.setText("Complete sign-in in the browser that just opened…")
        self.poller.start()

    def _poll_callback(self):
        if not self._result and not self._error:
            return
        self.poller.stop()
        result = self._result
        self._stop_server()
        if result.get("state") != self._state:
            self.status.setText("The authorization response could not be verified.")
            self.connect_button.setEnabled(True)
            return
        if result.get("error"):
            self.status.setText("Google authorization was cancelled or denied.")
            self.connect_button.setEnabled(True)
            return
        if not result.get("code"):
            return
        try:
            tokens = self._exchange_code(result["code"])
            access_token = tokens.get("access_token")
            if not access_token:
                raise RuntimeError("Google did not return an access token.")
            request = urllib.request.Request(
                USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            with urllib.request.urlopen(request, timeout=20) as response:
                identity = json.loads(response.read().decode("utf-8"))
            account = identity.get("email")
            if not isinstance(account, str) or not account:
                raise RuntimeError("Google did not return an account email.")
            keyring.set_password(
                SERVICE_NAME, f"{self.profile_id}:{account}",
                json.dumps({
                    "access_token": tokens.get("access_token"),
                    "refresh_token": tokens.get("refresh_token"),
                    "token_type": tokens.get("token_type", "Bearer"),
                    "scope": tokens.get("scope", SCOPES),
                    "expires_in": tokens.get("expires_in"),
                    "email": account,
                    "sub": identity.get("sub"),
                }),
            )
            self.status.setText(f"Connected Google account: {account}")
            self.info.setText(
                "Account connected. OAuth credentials are stored in the operating "
                "system credential store. This connection is for future Google API "
                "integrations; it does not sign the embedded web page into Gmail or YouTube."
            )
            self.connect_button.setText("Connected")
            self.accept()
        except Exception as exc:
            self.status.setText(f"Could not complete Google authorization: {exc}")
            self.connect_button.setEnabled(True)

    def _exchange_code(self, code: str) -> dict:
        payload = urllib.parse.urlencode({
            "client_id": self._client_id,
            "code": code,
            "code_verifier": self._verifier,
            "grant_type": "authorization_code",
            "redirect_uri": self._redirect_uri,
        }).encode("ascii")
        request = urllib.request.Request(
            TOKEN_URL, data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
        if not isinstance(result, dict):
            raise RuntimeError("Google returned an invalid token response.")
        return result

    def _stop_server(self):
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None

    def closeEvent(self, event):
        self.poller.stop()
        self._stop_server()
        super().closeEvent(event)
