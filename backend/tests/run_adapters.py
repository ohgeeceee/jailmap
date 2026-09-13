from pathlib import Path
from backend.adapters import bonneville_html, power_html, franklin_html, owyhee_pdf, jefferson_html


def load(name: str) -> bytes:
    return Path("/root/jailmap/backend/tests/fixtures", name).read_bytes()


bonneville_html._fetch_html = lambda url: load("bonneville_inmate_list.html")
power_html._fetch_html = lambda url: load("power_roster_list.html")
franklin_html._fetch_html = lambda url: load("franklin_roster_block.html")
owyhee_pdf._fetch_html = lambda url: load("owyhee_jail_page.html")
jefferson_html._fetch_html = lambda url: load("jefferson_roster_block.html")


def run(name, mod, source):
    try:
        result = mod.parse(source)
        print(name, "records=", len(result.records), "first_keys=", sorted(result.records[0].keys()) if result.records else [])
    except Exception as e:
        print(name, "ERROR", type(e).__name__, e)


run("bonneville", bonneville_html, {"county":"Bonneville","state":"ID","facility_name":"Bonneville County Jail","source_url":"http://bonnevillesheriff.com/bonneville-county-jail/inmate-list/","source_type":"custom_html"})
run("power", power_html, {"county":"Power","state":"ID","facility_name":"Power County Jail","source_url":"https://jail.powercounty.gov/jailroster/","source_type":"custom_html"})
run("franklin", franklin_html, {"county":"Franklin","state":"ID","facility_name":"Franklin County Jail","source_url":"https://www.franklinsheriff.org/roster.php","source_type":"custom_html"})
run("owyhee", owyhee_pdf, {"county":"Owyhee","state":"ID","facility_name":"Owyhee County Jail","source_url":"https://owyheecounty.net/sheriff/jail/","source_type":"pdf"})
