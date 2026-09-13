import sys
sys.path.insert(0, ".")
from bs4 import BeautifulSoup
from backend.adapters.idaho import _fetch_html
html = _fetch_html("http://inmateroster.lincolncountysheriff.us/").decode("utf-8", errors="ignore")
soup = BeautifulSoup(html, "html.parser")
tbody = soup.find_all("tbody")[0]
rows = tbody.find_all("tr")
current = []
for tr in rows[:15]:
    cells = tr.find_all(["td","th"])
    if tr.find("td", rowspan=True):
        print("=== BLOCK START ===")
        print("\n".join(current))
        print("=== BLOCK END ===\n")
        current = []
    current.append(" | ".join(cell.get_text("\n", strip=True) for cell in cells))
print("=== FINAL ===")
print("\n".join(current))
