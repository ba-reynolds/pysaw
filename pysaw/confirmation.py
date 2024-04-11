import time
from typing import List, Dict

from .utils import login_required
from .constants import ConfirmationTag
from .models import Confirmation, PysawBase


class ConfirmationExecutor(PysawBase):
    @login_required
    def fetch_confirmations(self) -> List[Confirmation]:
        tag = ConfirmationTag.CONF.value
        url = "https://steamcommunity.com/mobileconf/getlist"
        params = self._create_confirmation_params(tag)
        response = self._steam._session.get(url, params=params)

        confirmations = []
        response_json = response.json()

        for conf in response_json["conf"]:
            confirmation = Confirmation(
                conf["id"],
                conf["creator_id"],
                conf["nonce"],
                conf["headline"],
                conf["summary"][0],
                conf["creation_time"],
            )
            confirmations.append(confirmation)

        return confirmations

    @login_required
    def send_confirmation(self, confirmation: Confirmation, allow: bool = True) -> dict:
        tag = ConfirmationTag.ALLOW.value if allow else ConfirmationTag.CANCEL.value
        params = self._create_confirmation_params(tag)
        params |= {
            "op": tag,
            "ck": confirmation.nonce,
            "cid": confirmation.id,
        }
        url = "https://steamcommunity.com/mobileconf/ajaxop"
        return self._steam._session.get(url, params=params).json()

    def _create_confirmation_params(self, tag_string: str) -> Dict[str, str]:
        timestamp = int(time.time())
        android_id = self._steam.guard.generate_device_id()
        confirmation_key = self._steam.guard.generate_confirmation_key(
            tag_string, timestamp
        )
        return {
            "p": android_id,
            "a": self._steam.steamid,
            "k": confirmation_key,
            "t": timestamp,
            "m": "android",
            "tag": tag_string,
        }
