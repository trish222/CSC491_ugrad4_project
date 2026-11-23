"""Fetch and verify the exact MOOT input used in the development pilot."""
from hashlib import sha256
from urllib.request import urlopen

from pilot import DATA


URL = ("https://raw.githubusercontent.com/timm/moot/"
       "ca6163861db7b231824ecabc11b15a492b75df34/optimize/process/nasa93dem.csv")
EXPECTED = "506b16fbe880e0f4b59f6b98214e64b4ea56a307519aea84077290684996201a"


if __name__ == "__main__":
    with urlopen(URL, timeout=30) as source:
        data = source.read()
    if sha256(data).hexdigest() != EXPECTED:
        raise SystemExit("The download does not match the expected dataset checksum.")
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_bytes(data)
    print(DATA)
