import enum


class MarketListingStatus(enum.Enum):
    ACTIVE = enum.auto()
    ON_HOLD = enum.auto()
    TO_CONFIRM = enum.auto()


class CountryCode(enum.StrEnum):
    # https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
    ARGENTINA = "ar"
    UNITED_STATES = "us"


class CountryCurrency(enum.IntEnum):
    USD = 1
    ARS = 34


class StoreSort(enum.StrEnum):
    RELEVANCE = "_ASC"
    RELEASE_DATE = "Released_DESC"
    NAME = "Name_ASC"
    LOWEST_PRICE = "Price_ASC"
    HIGHEST_PRICE = "Price_DESC"
    USER_REVIEWS = "Reviews_DESC"
    STEAM_DECK_COMPATIBILITY = "DeckCompatDate_DESC"


class AppTypeFilter(enum.IntEnum):
    DEMOS = 10
    DOWNLOADABLE_CONTENT = 21
    SOUNDTRACKS = 990
    VIDEOS = 992
    HARDWARE = 993
    SOFTWARE = 994
    INCLUDE_BUNDLES = 996
    MODS = 997
    GAMES = 998


class FeaturesFilter(enum.IntEnum):
    VAC_ENABLED = 8
    CAPTIONS_AVAIBLE = 13
    INCLUDES_SOURCE_SDK = 16
    PARTIAL_CONTROLLER_SUPPORT = 18
    STEAM_ACHIEVEMENTS = 22
    STEAM_CLOUD = 23
    FULL_CONTROLLER_SUPPORT = 28
    STEAM_TRADING_CARDS = 29
    STEAMVR_COLLECTIBLES = 40
    REMOTE_PLAY_ON_PHONE = 41
    REMOTE_PLAY_ON_TABLET = 42
    REMOTE_PLAY_ON_TV = 43
    REMOTE_PLAY_TOGETHER = 44
    ADDITIONAL_HQ_AUDIO = 50
    STEAM_WORKSHOP = 51
    TRACKED_CONTROLLER_SUPPORT = 52


class ConfirmationTag(enum.StrEnum):
    CONF = "conf"
    DETAILS = "details"
    ALLOW = "allow"
    CANCEL = "cancel"


# Certain Steam responses will contain a price as an integer (instead of a float) where
# its last two digits are the decimals (e.g. 4550 -> 45.50), dividing the price by 100
# allows us to get "the real number" rather than the integer Steam gave us.
# ...And the other way around too, sometimes Steam expects you to send a price as an
# integer instead of a float (for example when creating a sell order on the market), so
# multiplying the price by 100 will give us the price Steam wants.
STEAM_FACTOR = 100
