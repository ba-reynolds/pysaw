from typing import Iterable, Iterator, TYPE_CHECKING

from .constants import MarketListingStatus


if TYPE_CHECKING:
    import pysaw


class Item:
    # https://dev.doctormckay.com/topic/332-identifying-steam-items/

    # --- APPID ---
    # Every item on Steam must be owned by an app. An "app" is a game, software, or
    # whatever on Steam. Every app has its own unique AppID.  For example, TF2's AppID
    # is 440 so TF2's store page can be found at http://store.steampowered.com/app/440.
    # Note that every single trading card on steam is owned by the "Steam" app, which
    # has AppID 753.

    # --- CONTEXTID ---
    # Of course, the AppID alone isn't enough. You also need two other IDs.
    # When you open your inventory, some games have a dropdown menu that allows
    # you to select a specific context, context id saves the id of that context.
    # See: https://i.imgur.com/oUTtIUk.png for an example.
    # If a game doesn't have a drop-down menu to select a context, that doesn't
    # mean that it's without contexts. That only means that it has one single
    # visible context. That single context still has an ID.

    # --- ASSETID ---
    # Every asset on Steam has, in addition to its AppID and context ID, an asset ID
    # which is guaranteed to be unique inside of a given AppID+ContextID combination.
    # An item's asset ID may be referred to as "assetid" or just plain "id".

    # --- CLASSID ---
    # The classid is all you need to get a general overview of an item. For example,
    # items with the same classid will pretty much always have the same name and image.

    # --- INSTANCEID ---
    # The instanceid allows you to get finer details such as how many kills are on a
    # strange/StatTrak weapon, or custom names/descriptions.

    # --- IDENTIFYING AN ITEM ---
    # In order to uniquely identify an item, you need its AppID, its context ID, and
    # its asset ID. Once you have these three things, only then can you uniquely
    # identify it
    def __init__(
        self,
        appid: str = None,
        contextid: str = None,
        assetid: str = None,
        classid: str = None,
        instanceid: str = None,
        market_hash_name: str = None,
    ):
        self.appid = appid
        self.contextid = contextid
        self.assetid = assetid
        self.classid = classid
        self.instanceid = instanceid
        self.market_hash_name = market_hash_name

    def __repr__(self) -> str:
        return "%s(appid=%s, market_hash_name=%s)" % (
            self.__class__.__name__,
            self.appid,
            self.market_hash_name,
        )


class Inventory:
    def __init__(self, items: Iterable[Item] = None):
        self._items = {}
        if items is not None:
            for item in items:
                self.add_item(item)

    def add_item(self, item: Item) -> None:
        appid, mkth = item.appid, item.market_hash_name

        if appid not in self._items:
            self._items[appid] = {}
        if mkth not in self._items[appid]:
            self._items[appid][mkth] = []

        self._items[appid][mkth].append(item)

    def remove_item(self, item: Item):
        appid, mkth = item.appid, item.market_hash_name
        self._items[appid][mkth].remove(item)
        if not self._items[appid][mkth]:
            del self._items[appid][mkth]

    def without_duplicates(self) -> Iterator[Item]:
        for appid in self._items:
            for mkth in self._items[appid]:
                yield self._items[appid][mkth][0]

    def __iter__(self):
        for appid in self._items:
            for mkth in self._items[appid]:
                yield from self._items[appid][mkth]

    def __len__(self):
        n = 0
        for _ in self:
            n += 1
        return n

    def __repr__(self) -> str:
        return "%s(num_items=%d)" % (self.__class__.__name__, len(self))


class MarketListing:
    def __init__(
        self,
        listingid: str,
        time_created: int,
        status: MarketListingStatus,
        item: Item,
        you_receive: float,
        buyer_pays: float,
    ):
        self.listingid = listingid
        self.time_created = time_created
        self.status = status
        self.item = item
        self.you_receive = you_receive
        self.buyer_pays = buyer_pays

    def __repr__(self) -> str:
        return "%s(item=%r, buyer_pays=%.2f)" % (
            self.__class__.__name__,
            self.item,
            self.buyer_pays,
        )


class Confirmation:
    def __init__(
        self,
        id: str,
        creator_id: str,
        nonce: str,
        summary: str,
        headline: str,
        creation_time: int,
    ):
        self.id = id
        self.creator_id = creator_id
        self.nonce = nonce
        self.summary = summary
        self.headline = headline
        self.creation_time = creation_time

    def __repr__(self) -> str:
        return "%s(id=%s, summary=%s)" % (
            self.__class__.__name__,
            self.id,
            self.summary,
        )


class PysawBase:
    def __init__(self, steam: "pysaw.Steam"):
        self._steam = steam
