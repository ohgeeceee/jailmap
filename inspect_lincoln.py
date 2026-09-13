import sys
sys.path.insert(0, ".")
from bs4 import BeautifulSoup
from backend.adapters.idaho import _fetch_html
html = _fetch_html("http://inmateroster.lincolncountysheriff.us/").decode("utf-8", errors="ignore")
soup = BeautifulSoup(html, "html.parser")
print("tbody", len(soup.find_all("tbody")))
for tb in soup.find_all("tbody"):
    rows = tb.find_all("tr")
    caption = tb.find_previous_sibling("caption")
    cap = caption.get_text(strip=True) if caption else ""
    print("tbody rows", len(rows), "caption", cap)
    for i, tr in enumerate(rows[:10]):
        cells = tr.find_all(["td","th"])
        print(i, [(c.name, c.get("rowspan"), c.get_text(strip=True)[:50]) for c in cells])
    print("---")
