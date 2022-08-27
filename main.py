from selectolax.parser import HTMLParser
import requests

BLOCKCHAINS = {
    "BSC": {
        "url": "https://bscscan.com",
    },
    "ETHER": {
        "url": "https://etherscan.io",
    },
    "POLYGON": {
        "url": "https://polygonscan.com",
    },
    "MOON": {
        "url": "https://moonscan.io",
    },
    "ARBI": {
        "url": "https://arbiscan.io",
    },
}


def get_headers(blockchain: str) -> dict:
    referer = BLOCKCHAINS[blockchain]["url"]
    return {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "referer": f"{referer}/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
    }


def get_page(url: str, blockchain: str) -> str:
    headers = get_headers(blockchain)
    return requests.get(url, headers=headers).text


def get_conracts(blockchain: str, all_pages: bool = True) -> dict:
    contracts = {}
    last_page = 6 if all_pages else 2
    url = BLOCKCHAINS[blockchain]["url"]
    for page in range(1, last_page):
        html = get_page(f"{url}/contractsVerified/{page}?ps=100", blockchain)
        tree = HTMLParser(html)
        table_body = tree.css_first("tbody")
        rows = table_body.css("tr")
        for row in rows:
            try:
                cols = row.css("td")
                balance, currency = cols[4].text().split()
                address = cols[0].text().strip()
                contracts[address] = {
                    "address": address,
                    "url": f"{url}/address/{address}#code",
                    "name": cols[1].text().strip(),
                    "compiler": cols[2].text().strip(),
                    "version": cols[3].text().strip(),
                    "balance": float(balance.strip()),
                    "currency": currency.strip(),
                    "transactions": int(cols[5].text().strip()),
                    "verified": cols[7].text().strip(),
                    "license": cols[9].text().strip(),
                }
            except:
                continue
    return contracts


if __name__ == "__main__":
    contracts = get_conracts("ARBI", True)
    for address, data in contracts.items():
        print(address, data["name"])
    print(len(contracts))
