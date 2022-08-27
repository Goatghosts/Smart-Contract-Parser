from selectolax.parser import HTMLParser
import requests


def get_headers(blockchain):
    return {
        "authority": f"{blockchain}",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "referer": f"https://{blockchain}/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
    }


def get_page(url, blockchain):
    headers = get_headers(blockchain)
    return requests.get(url, headers=headers).text


def get_conracts(blockchain, page):
    html = get_page(f"https://{blockchain}/contractsVerified/{page}?ps=100", blockchain)
    tree = HTMLParser(html)
    table_body = tree.css_first("tbody")
    rows = table_body.css("tr")
    contracts = []
    for row in rows:
        try:
            cols = row.css("td")
            balance, currency = cols[4].text().split()
            contracts.append(
                {
                    "address": cols[0].text().strip(),
                    "name": cols[1].text().strip(),
                    "compiler": cols[2].text().strip(),
                    "version": cols[3].text().strip(),
                    "balance": float(balance.strip()),
                    "currency": currency.strip(),
                    "transactions": int(cols[5].text().strip()),
                    "verified": cols[7].text().strip(),
                    "license": cols[9].text().strip(),
                }
            )
        except:
            continue
    return contracts


POOL = [
    "etherscan.io",
    "bscscan.com",
    "polygonscan.com",
    "moonscan.io",
    "arbiscan.io",
]

if __name__ == "__main__":
    for contract in get_conracts(POOL[4], 1):
        print(contract)
