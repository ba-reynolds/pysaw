# Python Steam API Wrapper (pysaw)

Python library designed to simplify and automate interactions with the Steam API. This wrapper provides a convenient interface for accessing various endpoints of the Steam API, reducing the manual effort required for integrating Steam functionalities into your projects.

## Obtaining your maFile

Use [SteamDesktopAuthenticator](https://github.com/Jessecar96/SteamDesktopAuthenticator).

## Examples

### Get your wallet's balance

```python
import pysaw

steam = pysaw.Steam(username="<user>", password="<pass>", steam_guard_path="<path>")
steam.login()
balance = steam.fetch_wallet_balance()
print(balance)
```

Outputs:
```
10.47
```

### Get an item's price on the market

```python
import pysaw

steam = pysaw.Steam()   # authentication is not required
price = steam.market.fetch_price(
    appid="440",
    market_hash_name="Mann Co. Supply Crate Key",
    currency=pysaw.CountryCurrency.USD
)
print(price)
```

Outputs:
```python
{
    "lowest_price": "$2.08",
    "volume": "20,378",
    "median_price": "$2.10"
}
```

### Store search using filters

```python
import pysaw

steam = pysaw.Steam()   # no authentication is required
games = steam.store.search(
    term="Shoot",
    maxprice=5,     # 5 USD
    cc=pysaw.CountryCode.UNITED_STATES,
    sort_by=pysaw.StoreSort.LOWEST_PRICE,
    features=[pysaw.FeaturesFilter.STEAM_ACHIEVEMENTS, pysaw.FeaturesFilter.STEAM_TRADING_CARDS],
    extract_all=True
)
print(games)
```

Outputs:
```python
{
    "865040": {"name": "Super Bit Blaster XL"},
    "525300": {"name": "Starship Annihilator"},
    "332480": {"name": "Phoenix Force"},
    "586350": {"name": "UBERMOSH:WRAITH"},
    "640380": {"name": "UBERMOSH Vol.5"},
    ...
}
```

### Get your sell listings on the market

```python
import pysaw

steam = pysaw.Steam(username="<user>", password="<pass>", steam_guard_path="<path>")
steam.login()

listings, listings_on_hold, listings_to_confirm = \
    steam.market.fetch_my_market_listings()
print(listings_to_confirm)
```

Outputs:
```python
[
    MarketListing(item=Item(appid=440, market_hash_name=Mann Co. Supply Crate Key), buyer_pays=2.14)
]
```

### Get yours/someone else's inventory

```python
import pysaw

# No authentication is required to get someone else's inventory (assuming
# its public)
steam = pysaw.Steam()
inventory = steam.market.fetch_inventory(steamid="", appid="", contextid="")

# Or if you are authenticated you can get your own inventory easily
steam = pysaw.Steam(username="<user>", password="<pass>", steam_guard_path="<path>")
steam.login()
steam.market.fetch_my_inventory(appid="", contextid="")
```

### Approve market listings pending confirmation

```python
import pysaw

steam = pysaw.Steam(username="<user>", password="<pass>", steam_guard_path="<path>")
steam.login()

_, _, listings_to_confirm = steam.market.fetch_my_market_listings()
confirmations = steam.confirmator.fetch_confirmations()

for listing in listings_to_confirm:
    for conf in confirmations:
        if listing.listingid == conf.creator_id:
            steam.confirmator.send_confirmation(conf, allow=True)
```

### Sell orders on the market

```python
import pysaw

steam = pysaw.Steam(username="<user>", password="<pass>", steam_guard_path="<path>")
steam.login()

# Create
inventory = steam.market.fetch_my_inventory(appid="440", contextid="")
for item in inventory:
    steam.market.create_sell_order(item, buyer_pays=3.14)

# Cancel
listings, listings_on_hold, listings_to_confirm = \
    steam.market.fetch_my_market_listings()
for listing in listings + listings_on_hold + listings_to_confirm:
    steam.market.cancel_sell_order(listing)
```

### Generate 2FA code

```python
import pysaw

steam = pysaw.Steam(steam_guard_path="<path>")
code = steam.guard.generate_one_time_code()
print(code)
```

Outpus:
```
M793M
```

### Purchase using your wallet's balance

```python
import pysaw

steam = pysaw.Steam(username="<user>", password="<pass>", steam_guard_path="<path>")
steam.login()

steam.store.add_to_cart(appid="1245620")
steam.store.purchase_cart()
```

## Installation

1. Clone this repository to your local machine and `cd` into it:

```bash
git clone https://github.com/ba-reynolds/steam-api-wrapper.git
cd steam-api-wrapper
```

2. Create a virtual environment, activate it and install the dependencies:
```bash
python3 -m venv venv
call venv/scripts/activate
pip install -r requirements.txt
```

3. Import the library for your own use:
```python
import pysaw

steam = pysaw.Steam(username="<user>", password="<pass>", steam_guard_path="<path>")
steam.login()
```