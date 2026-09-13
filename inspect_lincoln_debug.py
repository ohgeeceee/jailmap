import sys
sys.path.insert(0, ".")
from states.SD.counties.lincoln.adapter import _is_inmate_start, _build_inmate, _handle_value_row
from bs4 import BeautifulSoup
from backend.adapters.idaho import _fetch_html
html = _fetch_html("http://inmateroster.lincolncountysheriff.us/").decode("utf-8", errors="ignore")
soup = BeautifulSoup(html, "html.parser")
tbody = soup.find_all("tbody")[0]
rows = tbody.find_all("tr")
current = None
last_header = None
for i, tr in enumerate(rows[:15]):
    cells = tr.find_all(["td","th"])
    texts = [cell.get_text(strip=True)[:30] for cell in cells]
    is_start = _is_inmate_start(cells) if cells else False
    if is_start:
        if current:
            print("=== APPEND ===")
        current = _build_inmate(cells, {"state":"SD","county":"lincoln","facility":"Lincoln County Jail","source_url":"http://inmateroster.lincolncountysheriff.us/"}, "now")
        last_header = None
        print("START", i, texts)
    elif current is not None and cells:
        last_header, current = _handle_value_row(current, cells, last_header)
        print("ROW", i, texts, "=>", last_header)
    else:
        print("SKIP", i, texts)
if current:
    print("=== FINAL ===")
    print(current["booking_number"], current["booking_date"], current["charges"][0]["description"], current["notes"])
