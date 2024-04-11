import re
import json
import base64
from typing import List, Dict, TYPE_CHECKING

from .utils import login_required, n_elements_per_call, encode_varint
from .exceptions import TransactionError, NotEnoughFunds
from .constants import (
    StoreSort,
    AppTypeFilter,
    FeaturesFilter,
    CountryCode,
    STEAM_FACTOR,
)
from .models import PysawBase

if TYPE_CHECKING:
    import requests


class Store(PysawBase):
    @login_required
    def fetch_owned_apps(self) -> List[str]:
        url = "https://store.steampowered.com/dynamicstore/userdata/"
        response = self._steam._session.get(url)

        return list(map(str, response.json()["rgOwnedApps"]))

    @login_required
    def fetch_app_trading_cards(self, appid: str) -> List[str]:
        url = f"https://steamcommunity.com/my/ajaxgetbadgeinfo/{appid}"
        response = self._steam._session.get(url)
        try:
            response_json = response.json()
        except json.JSONDecodeError:
            return self.fetch_app_trading_cards(appid)

        if response_json == {"eresult": 1}:  # game doesn't have trading cards
            return []

        market_hash_names = []
        for tc in response_json["badgedata"]["rgCards"]:
            market_hash_names.append(tc["markethash"])

        return market_hash_names

    def fetch_app_price(self, appid: str) -> Dict[str, int]:
        return self.fetch_app_price_many([appid])[appid]

    def fetch_app_price_many(
        self, appids: List[str], cc: CountryCode = CountryCode.ARGENTINA
    ) -> Dict[str, Dict[str, int]]:
        url = "https://store.steampowered.com/api/appdetails/"
        prices = {}

        # There's no limit on how many apps we can request at once, but from
        # personal experience Steam seems to struggle (i.e. returns an error)
        # for anything above 500.
        for id in n_elements_per_call(appids, n=500):
            params = {
                "filters": "price_overview",
                "appids": ",".join(id),
                "cc": cc.value,
            }
            response = self._steam._session.get(url, params=params)
            prices |= self._parse_prices(response.json())

        return prices

    def fetch_app_packages(self, appid: str) -> List[int]:
        # Not sure if this rule always applies, but when you have a game, the package
        # at index 0 is usually the game itself, while the rest of the packages are
        # stuff like "game + game soundtrack"
        params = {"appids": appid}
        url = "https://store.steampowered.com/api/appdetails"
        response = self._steam._session.get(url, params=params)

        return response.json()[appid]["data"]["packages"]

    @login_required
    def add_to_cart(self, appid: str) -> None:
        url = "https://api.steampowered.com/IAccountCartService/AddItemsToCart/v1"
        params = {
            "access_token": self._steam._login_exec.access_token,
            "spoof_steamid": "",
        }

        # Hacky way to create the protobuf message expected by Steam
        # https://github.com/SteamDatabase/Protobufs/blob/6bf6fa0550f26cbaa329de2a576d2f61ee9172bd/webui/service_accountcart.proto#L34
        subid = self.fetch_app_packages(appid)[0]
        b64_protobuf = base64.b64encode(
            b"\x0a\x02\x41\x52\x12\x04\x08" + encode_varint(subid)
        )
        files = (("input_protobuf_encoded", (None, b64_protobuf)),)
        self._steam._session.post(url, params=params, files=files)

    @login_required
    def purchase_cart(self) -> None:
        response_init = self._init_transaction()
        if response_init.json()["success"] != 1:
            raise TransactionError("Error when initializing the transaction")

        transid = response_init.json()["transid"]
        response_info = self._info_transaction(transid)
        self._assert_enough_funds_to_purchase_cart(response_info)

        response_finalize = self._finalize_transaction(transid)
        if response_finalize.json()["success"] != 22:  # https://steamerrors.com/22
            raise TransactionError("Error when finalizing the transaction")

    @login_required
    def _init_transaction(self) -> "requests.Response":
        url = "https://checkout.steampowered.com/checkout/inittransaction/"
        data = {
            "PaymentMethod": "steamaccount",
            "sessionid": self._steam._sessionid,
            "bUseAccountCart": 1,
            "gidShoppingCart": -1,
            "sessionid": self._steam.sessionid,
        }
        response = self._steam._session.post(url, data=data)

        return response

    @login_required
    def _info_transaction(self, transid: str) -> "requests.Response":
        url = f"https://checkout.steampowered.com/checkout/getfinalprice/?transid={transid}"
        response = self._steam._session.get(url)

        return response

    @login_required
    def _finalize_transaction(self, transid: str) -> "requests.Response":
        url = "https://checkout.steampowered.com/checkout/finalizetransaction/"
        data = {"transid": transid}
        response = self._steam._session.post(url, data=data)

        return response

    @login_required
    def _assert_enough_funds_to_purchase_cart(
        self, response_info: "requests.Response"
    ) -> None:
        total = response_info.json()["total"] / STEAM_FACTOR
        funds = self._steam.fetch_wallet_balance()
        if total > funds:
            raise NotEnoughFunds(f"Have: {funds}, need: {total}")

    def search(
        self,
        term: str = "",
        count: int = 100,
        start: int = 0,
        maxprice: int = None,
        sort_by: StoreSort = StoreSort.RELEVANCE,
        app_types: List[AppTypeFilter] = None,
        features: List[FeaturesFilter] = None,
        cc: CountryCode = CountryCode.ARGENTINA,
        ignore_preferences: bool = True,
        extract_all: bool = False,
    ) -> Dict[str, Dict[str, str]]:
        count = 100 if extract_all else count
        app_types = app_types or []
        features = features or []

        params = {
            "term": term,
            "count": count,
            "start": start,
            "maxprice": maxprice,
            "sort_by": sort_by.value,
            "category1": ",".join(map(str, app_types)),
            "category2": ",".join(map(str, features)),
            "cc": cc.value,
            "ignore_preferences": int(ignore_preferences),
            "json": 1,
        }
        url = "https://store.steampowered.com/search/results/"
        response = self._steam._session.get(url, params=params)
        apps = self._parse_search(response.json())

        if apps and extract_all:
            return apps | self.search(
                term=term,
                count=count,
                start=start + count,
                maxprice=maxprice,
                sort_by=sort_by,
                app_types=app_types,
                features=features,
                cc=cc,
                ignore_preferences=ignore_preferences,
                extract_all=True,
            )
        return apps

    @staticmethod
    def _parse_search(response_json: dict) -> Dict[str, Dict[str, str]]:
        apps = {}
        for app in response_json["items"]:
            name = app["name"]
            search = re.search(r"/steam/apps/(\d+)/", app["logo"])
            if not search:
                continue
            appid = search.group(1)
            apps[appid] = {"name": name}

        return apps

    @staticmethod
    def _parse_prices(response_json: dict) -> Dict[str, Dict[str, int]]:
        prices = {}
        for appid in response_json:
            if not response_json[appid]["success"] or not response_json[appid]["data"]:
                # The game isn't available for your region / the game doesn't have a
                # price yet / the game is free.
                # Unfortunately we have no way of knowing which is which based on the
                # response ¯\_(ツ)_/¯.
                prices[appid] = {}
                continue
            price_overview = response_json[appid]["data"]["price_overview"]
            prices[appid] = {
                "initial_price": price_overview["initial"] / STEAM_FACTOR,
                "final_price": price_overview["final"] / STEAM_FACTOR,
                "discount_percent": price_overview["discount_percent"],
            }

        return prices
