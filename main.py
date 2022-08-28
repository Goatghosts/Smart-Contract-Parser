from selectolax.parser import HTMLParser
import requests
import json

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
                address = cols[0].text().strip()
                balance, currency = cols[4].text().split()
                contracts[address] = {
                    "blockchain": blockchain,
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


urls = [
    "https://bscscan.com/address/0xeca88125a5adbe82614ffc12d0db554e2e2867c8#code",  # 4 files, have tracker
    "https://bscscan.com/address/0x0879dB3A4c289b7e3DFbdbB8Eb9494b2fDd31941#code",  # 6 files, not have tracker
    "https://bscscan.com/address/0xa9A4B9D7A192E75bE989Ce5D5F824Ae98Eab93f9#code",  # 1 file, have tracker
    "https://bscscan.com/address/0x8fa73c986fe6a76fecfd878090cba9bcd5687b4e#code",  # 1 file, not have tracker
]


def main():
    contracts = get_conracts("ARBI", True)
    for address, data in contracts.items():
        print(address, data["name"])
    print(len(contracts))


def get_contract_data(url: str):
    html = get_page(url, "BSC")
    tree = HTMLParser(html)
    info_block = tree.css_first("div.row.mb-4")
    data = {}
    rows = info_block.css("div.row.align-items-center")
    balance = rows[0].css_first("div.col-md-8")
    if balance:
        data["crypto_balance"] = balance.text().strip()
    balance = rows[1].css_first("div.col-md-8")
    if balance:
        data["fiat_balance"] = balance.text().strip()

    for row in rows:
        tokens_balance = row.css_first("a#availableBalanceDropdown")
        if tokens_balance:
            data["tokens_balance"] = tokens_balance.text(deep=False).strip()
            tokens_count = row.css_first("span")
            if tokens_count:
                data["tokens_count"] = tokens_count.text(deep=False).strip()
        creator_address = row.css_first('a[title="Creator Address"]')
        if creator_address:
            data["creator_address"] = creator_address.attributes["href"]
            creator_txn = row.css_first('a[title="Creator Txn Hash"]')
            if creator_txn:
                data["creator_txn"] = creator_txn.attributes["href"]
        token = row.css_first('a[title$="Token Tracker Page"]')
        if token:
            data["token"] = token.attributes["href"]

    print(json.dumps(data, indent=2))

    code_block = tree.css_first("div#dividcode")
    for i, code in enumerate(code_block.css("pre.editor")):
        print(i)
        print(code.text())
    print("-----------------------------------------------------------------")


if __name__ == "__main__":
    for url in urls:
        get_contract_data(url)
