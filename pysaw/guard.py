import base64
import hmac
import json
import struct
import time
import uuid
from hashlib import sha1
from typing import TYPE_CHECKING

from . import models


if TYPE_CHECKING:
    import pysaw


class SteamGuard(models.PysawBase):
    def __init__(self, steam: "pysaw.Steam", steam_guard_path: str | None) -> None:
        super().__init__(steam)
        self.guard = self._load_steam_guard_file(steam_guard_path)

    def generate_one_time_code(self, timestamp: int = None) -> str:
        if timestamp is None:
            timestamp = int(time.time())
        shared_secret = self.guard["shared_secret"]
        time_buffer = struct.pack(">Q", timestamp // 30)  # pack as Big endian, uint64
        time_hmac = hmac.new(
            base64.b64decode(shared_secret), time_buffer, digestmod=sha1
        ).digest()
        begin = ord(time_hmac[19:20]) & 0xF
        full_code = (
            struct.unpack(">I", time_hmac[begin : begin + 4])[0] & 0x7FFFFFFF
        )  # unpack as Big endian uint32
        chars = "23456789BCDFGHJKMNPQRTVWXY"
        code = ""

        for _ in range(5):
            full_code, i = divmod(full_code, len(chars))
            code += chars[i]

        return code

    def generate_confirmation_key(self, tag: str, timestamp: int = None) -> str:
        if timestamp is None:
            timestamp = int(time.time())
        identity_secret = self.guard["identity_secret"]
        buffer = struct.pack(">Q", timestamp) + tag.encode("ascii")
        return base64.b64encode(
            hmac.new(base64.b64decode(identity_secret), buffer, digestmod=sha1).digest()
        ).decode("ascii")

    @staticmethod
    def generate_device_id() -> str:
        return "android:" + str(uuid.uuid4())

    @staticmethod
    def _load_steam_guard_file(steam_guard_path: str | None) -> dict:
        if steam_guard_path is None:
            return {}
        with open(steam_guard_path, "r") as f:
            return json.load(f)
