import requests
from bs4 import BeautifulSoup

from . import guard
from . import market
from . import login
from . import store
from . import confirmation
from .utils import formatted_to_float, login_required


class Steam:
    def __init__(
        self, username: str = None, password: str = None, steam_guard_path: str = None
    ):
        self._username = username
        self._password = password
        self._session = requests.Session()
        self._steamid = ""
        self._sessionid = ""
        self._was_login_executed = False
        self._login_exec = login.LoginExecutor(self)

        self.guard = guard.SteamGuard(self, steam_guard_path)
        self.store = store.Store(self)
        self.market = market.SteamMarket(self)
        self.confirmator = confirmation.ConfirmationExecutor(self)

    def login(self) -> None:
        self._login_exec.login()
        self._was_login_executed = True

    @property
    @login_required
    def sessionid(self) -> str:
        if not self._sessionid:
            self._sessionid = self._session.cookies.get(
                "sessionid", domain="steamcommunity.com"
            )
        return self._sessionid

    @property
    @login_required
    def steamid(self) -> str:
        if not self._steamid:
            self._steamid = self._session.cookies.get(
                "steamLoginSecure", domain="steamcommunity.com"
            ).split("%7C%7")[0]
        return self._steamid

    @login_required
    def fetch_wallet_balance(self) -> float:
        url = "https://store.steampowered.com/account/"
        response = self._session.get(url)

        soup = BeautifulSoup(response.text, "html.parser")
        balance_formatted = soup.find("div", class_="accountData price").text

        return formatted_to_float(balance_formatted)

    @login_required
    def is_session_alive(self) -> bool:
        url = "https://steamcommunity.com/actions/EmoticonData"
        response = self._session.head(url, headers={"Connection": ""})

        return response.status_code == 200  # 401 if logged out
