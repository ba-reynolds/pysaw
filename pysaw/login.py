import base64
from typing import Tuple, TYPE_CHECKING

import rsa

from .models import PysawBase


if TYPE_CHECKING:
    import pysaw
    import requests


class LoginExecutor(PysawBase):
    def __init__(self, steam: "pysaw.Steam"):
        super().__init__(steam)
        self.refresh_token = ""
        self.access_token = ""

    def login(self) -> "requests.Session":
        # 1. Fetch rsa public key
        # 2. Begin auth session
        # 3. Update auth session (with steam guard code)
        # 4. Poll auth session
        # 5. Finalize login
        # 6. Set tokens

        begin_auth_session_response = self._begin_auth_session()
        self._update_auth_session_with_guard_code(begin_auth_session_response)
        finalize_login_response = self._finalize_login(self.refresh_token)
        self._set_tokens(finalize_login_response)
        self._set_sessionid_cookies()

    def _begin_auth_session(self) -> "requests.Response":
        rsa_key, rsa_timestamp = self._get_rsa_public_key()
        encrypted_password = self._encrypt_password(rsa_key)
        request_data = {
            "persistence": 1,
            "encrypted_password": encrypted_password,
            "encryption_timestamp": rsa_timestamp,
            "account_name": self._steam._username,
        }
        url = "https://api.steampowered.com/IAuthenticationService/BeginAuthSessionViaCredentials/v1"
        return self._steam._session.post(url, data=request_data)

    def _get_rsa_public_key(self) -> Tuple[rsa.PublicKey, int]:
        params = {"account_name": self._steam._username}
        url = "https://api.steampowered.com/IAuthenticationService/GetPasswordRSAPublicKey/v1"
        response = self._steam._session.get(url, params=params)
        response_json = response.json()

        rsa_mod = int(response_json["response"]["publickey_mod"], 16)
        rsa_exp = int(response_json["response"]["publickey_exp"], 16)
        rsa_timestamp = response_json["response"]["timestamp"]
        rsa_key = rsa.PublicKey(rsa_mod, rsa_exp)

        return rsa_key, rsa_timestamp

    def _update_auth_session_with_guard_code(
        self, begin_auth_session_response: "requests.Response"
    ) -> str:
        response_json = begin_auth_session_response.json()
        client_id = response_json["response"]["client_id"]
        steamid = response_json["response"]["steamid"]
        request_id = response_json["response"]["request_id"]
        code_type = response_json["response"]["allowed_confirmations"][0][
            "confirmation_type"
        ]

        # TODO: what happens if an account doesn't have guard activated?
        # TODO: what happens if we enter wrong credentials?
        code = self._steam.guard.generate_one_time_code()
        data = {
            "client_id": client_id,
            "steamid": steamid,
            "code_type": code_type,
            "code": code,
        }
        self._steam._session.post(
            "https://api.steampowered.com/IAuthenticationService/UpdateAuthSessionWithSteamGuardCode/v1",
            data=data,
        )

        return self._poll_auth_session(client_id, request_id)

    def _poll_auth_session(self, client_id: str, request_id: str) -> None:
        data = {"client_id": client_id, "request_id": request_id}
        response = self._steam._session.post(
            "https://api.steampowered.com/IAuthenticationService/PollAuthSessionStatus/v1",
            data=data,
        )
        response_json = response.json()
        self.refresh_token = response_json["response"]["refresh_token"]
        self.access_token = response_json["response"]["access_token"]

    def _finalize_login(self, refresh_token: str) -> "requests.Response":
        redir_url = "https://steamcommunity.com/login/home?goto="
        data = {"nonce": refresh_token, "redir": redir_url}
        response = self._steam._session.post(
            "https://login.steampowered.com/jwt/finalizelogin", data=data
        )
        return response

    def _encrypt_password(self, rsa_key: rsa.PublicKey) -> bytes:
        password = self._steam._password
        return base64.b64encode(rsa.encrypt(password.encode("utf-8"), rsa_key))

    def _set_tokens(self, finalize_login_response: "requests.Response") -> None:
        response_json = finalize_login_response.json()
        data = {"steamID": response_json["steamID"], "nonce": None, "auth": None}

        for site in response_json["transfer_info"]:
            url = site["url"]
            data["nonce"] = site["params"]["nonce"]
            data["auth"] = site["params"]["auth"]
            self._steam._session.post(url, data=data)

    def _set_sessionid_cookies(self) -> None:
        # After calling `self._set_tokens()`, only help.steampowered.com gives
        # us a sessionid cookie, use that cookie for the other domains.
        # The sessionid cookie is just a CSRF token, so we could use anything,
        # but let's use that sessionid for the sake of consistency.
        sessionid = self._steam._session.cookies.get(
            "sessionid", domain="help.steampowered.com"
        )
        domains = (
            "steamcommunity.com",
            "store.steampowered.com",
            "checkout.steampowered.com",
        )
        for domain in domains:
            self._steam._session.cookies.set("sessionid", sessionid, domain=domain)
