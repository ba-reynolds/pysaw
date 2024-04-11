from typing import Tuple, List, Dict, TYPE_CHECKING

from .models import MarketListing, Inventory, Item, PysawBase
from .utils import formatted_to_float, login_required
from .constants import MarketListingStatus, CountryCurrency, STEAM_FACTOR


if TYPE_CHECKING:
    import requests


class SteamMarket(PysawBase):
    @login_required
    def fetch_my_market_listings(self, start=0) -> Tuple[List[MarketListing]]:
        url = "https://steamcommunity.com/market/mylistings/"
        params = {"count": 100, "norender": 1, "start": start}
        response = self._steam._session.get(url, params=params)
        response_json = response.json()

        listings = self._parse_listings(
            response_json["listings"], MarketListingStatus.ACTIVE
        )
        listings_on_hold = self._parse_listings(
            response_json["listings_on_hold"], MarketListingStatus.ON_HOLD
        )
        listings_to_confirm = self._parse_listings(
            response_json["listings_to_confirm"], MarketListingStatus.TO_CONFIRM
        )

        if start + 100 < response_json["num_active_listings"]:
            a, b, c = self.fetch_my_market_listings(start=start + 100)
            listings += a
            listings_on_hold += b
            listings_to_confirm += c

        return listings, listings_on_hold, listings_to_confirm

    @login_required
    def create_sell_order(self, item: Item, buyer_pays: float) -> "requests.Response":
        url = "https://steamcommunity.com/market/sellitem/"
        headers = {
            "Referer": f"https://steamcommunity.com/profiles/{self._steam.steamid}/inventory/"
        }
        data = {
            "sessionid": self._steam._sessionid,
            "contextid": item.contextid,
            "assetid": item.assetid,
            "appid": item.appid,
            "price": int(round(buyer_pays / 1.15, 2) * STEAM_FACTOR),
            "amount": 1,  # used for stackable items
        }
        response = self._steam._session.post(url, data=data, headers=headers)

        return response

    @login_required
    def cancel_sell_order(self, listing: MarketListing) -> "requests.Response":
        url = f"https://steamcommunity.com/market/removelisting/{listing.listingid}"
        data = {"sessionid": self._steam._sessionid}
        headers = {"Referer": "https://steamcommunity.com/market/"}
        response = self._steam._session.post(url, data=data, headers=headers)

        return response

    @login_required
    def fetch_price_history(self, appid: str, market_hash_name: str) -> dict:
        url = "https://steamcommunity.com/market/pricehistory/"
        params = {"appid": appid, "market_hash_name": market_hash_name}
        response = self._steam._session.get(url, params=params)

        return response.json()

    def fetch_price(
        self,
        appid: str,
        market_hash_name: str,
        currency: CountryCurrency = CountryCurrency.ARS,
    ) -> Dict[str, float | None]:
        url = "https://steamcommunity.com/market/priceoverview"
        params = {
            "currency": currency.value,
            "appid": appid,
            "market_hash_name": market_hash_name,
        }
        response = self._steam._session.get(url, params=params)

        # If Steam can't fetch a value then it won't put it in the response
        # We add them so the user can expect some level of consistency
        response_json = response.json()
        if "lowest_price" in response_json:
            response_json["lowest_price"] = formatted_to_float(
                response_json["lowest_price"]
            )
        else:
            response_json["lowest_price"] = None

        if "median_price" in response_json:
            response_json["median_price"] = formatted_to_float(
                response_json["median_price"]
            )
        else:
            response_json["median_price"] = None

        if "volume" not in response_json:
            response_json["volume"] = None

        return response_json

    @login_required
    def fetch_my_inventory(self, appid: str, contextid: str) -> Inventory:
        return self.fetch_inventory(self._steam.steamid, appid, contextid)

    def fetch_inventory(self, steamid: str, appid: str, contextid: str) -> Inventory:
        url = f"https://steamcommunity.com/inventory/{steamid}/{appid}/{contextid}"
        params = {"l": "english", "count": 5000}
        response = self._steam._session.get(url, params=params)
        response_json = response.json()

        description_to_mkth_map = {}
        for desc in response_json["descriptions"]:
            key = desc["classid"] + "_" + desc["instanceid"]
            description_to_mkth_map[key] = desc["market_hash_name"]

        inventory = Inventory()
        for asset in response_json["assets"]:
            key = asset["classid"] + "_" + asset["instanceid"]
            item = Item(
                appid=asset["appid"],
                contextid=asset["contextid"],
                assetid=asset["assetid"],
                classid=asset["classid"],
                instanceid=asset["instanceid"],
                market_hash_name=description_to_mkth_map[key],
            )
            inventory.add_item(item)

        return inventory

    @staticmethod
    def _parse_listings(
        list_of_listings: List[dict], status: MarketListingStatus
    ) -> List[MarketListing]:

        listings = []
        for listing_dict in list_of_listings:
            item = Item(
                appid=listing_dict["asset"]["appid"],
                contextid=listing_dict["asset"]["contextid"],
                assetid=listing_dict["asset"]["id"],
                classid=listing_dict["asset"]["classid"],
                instanceid=listing_dict["asset"]["instanceid"],
                market_hash_name=listing_dict["asset"]["market_hash_name"],
            )
            listing = MarketListing(
                listingid=listing_dict["listingid"],
                time_created=listing_dict["time_created"],
                status=status,
                item=item,
                you_receive=listing_dict["price"] / STEAM_FACTOR,
                buyer_pays=(listing_dict["price"] + listing_dict["fee"]) / STEAM_FACTOR,
            )
            listings.append(listing)

        return listings
