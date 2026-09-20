#!/usr/bin/env python3
"""Fix html_roster jurisdictions: classify, update URLs, disable search-only."""
import re
import sys
from urllib.parse import urljoin

sys.path.insert(0, '/root/jailmap')
from backend.adapters.idaho import _fetch_html
from backend.adapters.html_roster import _TableExtractor, _map_columns

# All 80 html_roster jurisdictions from DB
JURISDICTIONS = [
    ("AK", "Statewide", "https://doc.alaska.gov/"),
    ("AL", "Winston County", "https://winstonal.gov/new_page3/sheriff_office.php"),
    ("AR", "Cleburne", "https://www.cleburnearso.gov/detention-center"),
    ("AR", "Faulkner", "https://www.fcso.ar.gov/inmate-roster/disclaim"),
    ("AR", "Fulton", "https://www.fultoncountyar.gov/inmate-roster"),
    ("AR", "Washington", "https://www.washcosoar.gov/res/DetaineeAlphaRoster.aspx"),
    ("AZ", "Maricopa", "https://maricopacountycourt.org/jail-roster/"),
    ("AZ", "Pima", "https://www.sheriff.pima.gov/inmate/"),
    ("CA", "Alameda", "https://www.alamedacountyca.gov/sheriff_app/"),
    ("CA", "Alpine County", "https://alpinecountyca.gov/700/Search-Rescue"),
    ("CA", "Contra Costa", "https://inmateinfo.so.cccounty.us/Web/InCustodyLocator"),
    ("CA", "Kern", "https://www.kerncountysheriff.org/roster/"),
    ("CA", "Orange", "https://www.ocsheriff.gov/inmate_information_system"),
    ("CA", "Sacramento", "https://apps.sacsheriff.com/Roster/"),
    ("CA", "San Bernardino", "https://wp.sbcounty.gov/sheriff/corrections/inmate-locator/"),
    ("CA", "Statewide", "https://ciris.mt.cdcr.ca.gov/"),
    ("CA", "Ventura", "https://sheriff.venturacounty.gov/inmate-information/inmate-search/"),
    ("CO", "El Paso", "https://www.epcsheriffsoffice.com/inmate-search"),
    ("DE", "Delaware County", "https://delcosheriff.org/inmate-search"),
    ("DE", "Kent County", "https://i2g.uslandrecords.com/DE/Kent2/D/Default.aspx"),
    ("GA", "Gilmer County", "https://gilmersheriffga.gov/"),
    ("HI", "Honolulu", "https://honolulucountycourt.us/inmate-search"),
    ("IA", "Cerro Gordo County", "https://sofiles.cerrogordo.gov/inmate_report/"),
    ("IA", "Polk", "https://www.polkcountyiowa.gov/sheriff/inmate-search/"),
    ("IA", "Woodbury County", "https://injail.wcicc.com/"),
    ("IL", "St. Clair", "https://www.co.st-clair.il.us/departments/sheriffs-department/corrections"),
    ("IN", "Lake", "https://www.lakecountysheriff.com/inmate-search"),
    ("IN", "Marion", "https://www.indy.gov/activity/inmate-search"),
    ("KS", "Sedgwick", "https://www.sedgwick.org/sheriff/inmate-search"),
    ("KY", "Fayette", "https://www.fayettesheriff.com/inmate-search"),
    ("LA", "East Baton Rouge", "https://www.ebrsheriff.org/inmate-search"),
    ("MA", "Plymouth", "https://plymouthcountysheriff.com/inmate-roster/"),
    ("MA", "Worcester", "https://inmatesearch.wcsoma.org/"),
    ("ME", "Kennebec", "https://kennebec.gov/sheriff/corrections/inmates-current/"),
    ("ME", "Penobscot", "https://www.penobscot-sheriff.net/inmates"),
    ("MN", "Marshall County", "https://www.marshallcountymn.gov/departments/sheriff/index.php"),
    ("MN", "Statewide", "https://coms.doc.state.mn.us/PublicViewer"),
    ("MO", "Cedar County", "https://cedarcountymo.gov/sheriff"),
    ("MO", "Daviess County", "https://daviessmosheriff.gov/"),
    ("MO", "Jackson", "https://www.jacksoncountysheriff.org/inmate-search"),
    ("MO", "Jasper County", "https://jaspercountysheriff.org/about-us/jasper-county-law-enforcement-memorial/"),
    ("MO", "Mercer County", "https://mercercountysheriffmo.gov/"),
    ("MS", "Hinds", "https://www.hindscountysheriff.com/inmate-search"),
    ("MS", "Lamar County", "https://lamarcountyms.gov/ms/so/"),
    ("MT", "Beaverhead County", "https://beaverheadcountymt.gov/departments/sheriff/"),
    ("MT", "Rosebud County", "https://rosebudcountymt.gov/departments/sheriff/"),
    ("NC", "Cumberland", "https://cumberlandsheriffnc.gov/active-inmate-page/"),
    ("NC", "Martin County", "https://webapps.doc.state.nc.us/opi/offendersearch.do?method=view"),
    ("NC", "Robeson County", "https://www.ustaxdata.com/nc/robeson/robesontaxSearch.cfm"),
    ("ND", "Stutsman", "https://www.stutsmancounty.gov/departments/correctional-center/inmate-roster/"),
    ("NE", "Madison", "https://madisonsheriffne.gov/inmate-roster/"),
    ("NH", "Coos County", "https://www.cooscountynh.gov/government/departments/sheriffs_department.php"),
    ("NH", "Rockingham", "https://rockinghamcountynh.org/departments/corrections/inmate-information/"),
    ("NJ", "Burlington County", "https://salesweb.civilview.com/Sales/SalesSearch?countyId=3"),
    ("NJ", "Essex", "https://essexcountynj.org/sheriff/inmate-information/"),
    ("NJ", "Hudson", "https://www.hudsoncountysheriff.com/inmate-search"),
    ("NJ", "Middlesex", "https://www.middlesexcountynj.gov/government/departments/department-of-public-safety-and-health/office-of-adult-correction-and-youth-services/adult-corrections/inmate-lookup"),
    ("NJ", "Morris County", "https://salesweb.civilview.com/Sales/SalesSearch?countyId=9"),
    ("NJ", "Ocean", "https://coroms.co.ocean.nj.us:8087/IML"),
    ("NM", "Santa Fe", "https://www.santafecountynm.gov/corrections/adultfacility/inmate-lookup"),
    ("NV", "Clark", "https://www.clarkcountynv.gov/government/departments/detention_center/"),
    ("NY", "New York City", "https://www.nyc.gov/site/doc/inmate-info/inmate-lookup.page"),
    ("NY", "Oneida", "https://sheriff.oneidacountyny.gov/quick-links/inmate-list/"),
    ("NY", "Westchester", "https://correction.westchestercountyny.gov/westchester-inmate-search"),
    ("OH", "Cuyahoga", "https://www.cuyahogacounty.us/sheriff/inmate-search"),
    ("OH", "Lake County", "https://www.lakecountyohio.gov/sheriff/"),
    ("OH", "Logan County", "https://www.logancountyohio.gov/sheriff.html"),
    ("OH", "Mercer County", "https://inmate.mercercountysheriffohio.gov"),
    ("OH", "Miami County", "https://miami.miamivalleyjails.org/"),
    ("OH", "Muskingum County", "https://salesweb.civilview.com/Sales/SalesSearch?countyId=27"),
    ("OK", "Oklahoma", "https://www.oklahomacountysheriff.org/inmate-search"),
    ("OK", "Tulsa", "https://www.tulsacountysheriff.org/inmate-search"),
    ("PA", "Statewide", "https://inmatelocator.cor.pa.gov/"),
    ("TN", "Knox", "https://sheriff.knoxcountytn.gov/inmate.php"),
    ("TN", "Van Buren County", "https://vanburencountytn.gov/"),
    ("TX", "Harris", "https://harriscountyso.org/JailInfo/Default"),
    ("TX", "Tarrant", "https://inmatesearch.tarrantcounty.com/"),
    ("TX", "Travis", "https://www.tcsheriff.org/inmate-jail-info/inmate-info/find-an-inmate"),
    ("UT", "Iron County", "https://ironsheriffut.gov/jail/inmate-bookings"),
    ("UT", "Salt Lake", "https://www.slcsheriff.org/inmate-search"),
    ("VA", "Henrico", "https://henrico.gov/services/henrico-inmate-search/"),
    ("VA", "Roanoke", "https://inmateinquiry.roanokecountyva.gov/Roanoke"),
    ("VA", "Virginia Beach", "https://virginiabeach.gov/services/public-safety/sheriffs-office"),
    ("WA", "Clark", "https://clark.wa.gov/jail-services/jail-roster"),
    ("WA", "King", "https://kingcounty.gov/depts/sheriff/inmate-info.aspx"),
    ("WI", "Dane", "https://www.danesheriff.com/inmate-search"),
    ("WI", "Milwaukee", "https://www.milwaukee.gov/sheriff/Inmate-Information"),
    ("WV", "Brooke County", "https://brooke.softwaresystems.com/index.html"),
    ("WV", "Monongalia County", "https://monongalia.softwaresystems.com/index.html"),
    ("WV", "Wirt County", "https://wirtcountywvsheriff.gov/active-warrant-list"),
]

# Known correct URLs for jurisdictions that have wrong source_url
URL_FIXES = {
    ("AR", "Cleburne"): "https://www.cleburnearso.gov/detention-center",  # search form
    ("AR", "Faulkner"): "https://www.fcso.ar.gov/inmate-roster/disclaim",  # search form
    ("AR", "Washington"): "https://www.washcosoar.gov/res/DetaineeAlphaRoster.aspx",  # search form
    ("CA", "Alpine County"): "https://alpinecountyca.gov/700/Search-Rescue",  # no roster
    ("CA", "Kern"): "https://www.kerncountysheriff.org/roster/",  # domain for sale
    ("CA", "Ventura"): "https://sheriff.venturacounty.gov/inmate-information/inmate-search/",  # WAF blocked
    ("GA", "Gilmer County"): "https://gilmersheriffga.gov/",  # file listing
    ("MO", "Cedar County"): "https://omsweb.public-safety-cloud.com/jtclientweb/jailtracker/index/Cedar_County_MO",  # JailTracker
    ("MO", "Jackson"): "https://www.jacksoncountysheriff.org/inmate-search",  # search form
    ("MS", "Lamar County"): "https://lamarcountyms.gov/ms/so/",  # no roster
    ("MT", "Beaverhead County"): "https://beaverheadcountymt.gov/departments/sheriff/",  # no roster
    ("MT", "Rosebud County"): "https://rosebudcountymt.gov/departments/sheriff/",  # no roster
    ("NC", "Cumberland"): "https://cumberlandsheriffnc.gov/active-inmate-page/",  # search form
    ("ND", "Stutsman"): "https://www.stutsmancounty.gov/departments/correctional-center/inmate-roster/",  # search form
    ("NE", "Madison"): "https://madisonsheriffne.gov/inmate-roster/",  # search form
    ("NH", "Rockingham"): "https://rockinghamcountynh.org/departments/corrections/inmate-information/",  # search form
    ("OH", "Cuyahoga"): "https://www.cuyahogacounty.us/sheriff/inmate-search",  # search form
    ("OH", "Logan County"): "https://www.logancountyohio.gov/sheriff.html",  # no roster
    ("TX", "Harris"): "https://harriscountyso.org/JailInfo/Default",  # Angular app
    ("UT", "Iron County"): "https://ironsheriffut.gov/jail/inmate-bookings",  # search form
    ("UT", "Salt Lake"): "https://www.slcsheriff.org/inmate-search",  # search form
    ("VA", "Virginia Beach"): "https://virginiabeach.gov/services/public-safety/sheriffs-office",  # no roster
    ("WA", "Clark"): "https://clark.wa.gov/jail-services/jail-roster",  # search form
    ("WA", "King"): "https://kingcounty.gov/depts/sheriff/inmate-info.aspx",  # search form
    ("WV", "Brooke County"): "https://brooke.softwaresystems.com/index.html",  # no roster
    ("WV", "Wirt County"): "https://wirtcountywvsheriff.gov/active-warrant-list",  # no roster
}

# Jurisdictions confirmed to have table-based rosters (from earlier probe)
TABLE_ROSTER = {
    ("AL", "Winston County"),
    ("DE", "Kent County"),
    ("IA", "Woodbury County"),
    ("NC", "Martin County"),
    ("NC", "Robeson County"),
    ("NJ", "Ocean"),
    ("OH", "Miami County"),
    ("OH", "Muskingum County"),
    ("TN", "Van Buren County"),
    ("WV", "Monongalia County"),
}

# Jurisdictions confirmed to be GovernmentWebsite (div-based)
GOV_WEBSITE = {
    ("AR", "Carroll"),
    ("AR", "Poinsett"),
}

# Jurisdictions that are search-form-only (can't scrape)
SEARCH_FORM_ONLY = {
    ("AZ", "Maricopa"),
    ("AZ", "Pima"),
    ("CA", "Alameda"),
    ("CA", "Contra Costa"),
    ("CA", "Orange"),
    ("CA", "Sacramento"),
    ("CA", "San Bernardino"),
    ("CO", "El Paso"),
    ("HI", "Honolulu"),
    ("IL", "St. Clair"),
    ("IN", "Lake"),
    ("MA", "Worcester"),
    ("NM", "Santa Fe"),
    ("NY", "New York City"),
    ("NY", "Oneida"),
    ("NY", "Westchester"),
    ("TN", "Knox"),
    ("TX", "Tarrant"),
    ("TX", "Travis"),
    ("VA", "Roanoke"),
    ("VA", "Virginia Beach"),
    ("WA", "Clark"),
}

# Jurisdictions with no roster at all (wrong URL, domain for sale, etc.)
NO_ROSTER = {
    ("AK", "Statewide"),
    ("CA", "Alpine County"),
    ("CA", "Kern"),
    ("CA", "Statewide"),
    ("CA", "Ventura"),
    ("GA", "Gilmer County"),
    ("IA", "Cerro Gordo County"),
    ("IA", "Polk"),
    ("IN", "Marion"),
    ("KS", "Sedgwick"),
    ("KY", "Fayette"),
    ("LA", "East Baton Rouge"),
    ("ME", "Kennebec"),
    ("ME", "Penobscot"),
    ("MN", "Marshall County"),
    ("MN", "Statewide"),
    ("MO", "Cedar County"),
    ("MO", "Daviess County"),
    ("MO", "Jasper County"),
    ("MO", "Mercer County"),
    ("MS", "Hinds"),
    ("MS", "Lamar County"),
    ("MT", "Beaverhead County"),
    ("MT", "Rosebud County"),
    ("NC", "Cumberland"),
    ("ND", "Stutsman"),
    ("NE", "Madison"),
    ("NH", "Coos County"),
    ("NH", "Rockingham"),
    ("NJ", "Burlington County"),
    ("NJ", "Essex"),
    ("NJ", "Hudson"),
    ("NJ", "Middlesex"),
    ("NJ", "Morris County"),
    ("NV", "Clark"),
    ("OH", "Cuyahoga"),
    ("OH", "Lake County"),
    ("OH", "Logan County"),
    ("OH", "Mercer County"),
    ("OK", "Oklahoma"),
    ("OK", "Tulsa"),
    ("PA", "Statewide"),
    ("TX", "Harris"),
    ("UT", "Iron County"),
    ("UT", "Salt Lake"),
    ("WA", "King"),
    ("WI", "Dane"),
    ("WI", "Milwaukee"),
    ("WV", "Brooke County"),
    ("WV", "Wirt County"),
}


def main():
    print("=== HTML ROSTER JURISDICTION FIX ===\n")
    
    # Verify all jurisdictions are accounted for
    all_juris = set((s, c) for s, c, _ in JURISDICTIONS)
    accounted = set()
    for s in [TABLE_ROSTER, GOV_WEBSITE, SEARCH_FORM_ONLY, NO_ROSTER]:
        accounted |= s
    
    missing = all_juris - accounted
    if missing:
        print(f"WARNING: {len(missing)} jurisdictions not accounted for:")
        for m in sorted(missing):
            print(f"  {m}")
    
    print(f"\nTable roster (enable): {len(TABLE_ROSTER)}")
    print(f"GovernmentWebsite: {len(GOV_WEBSITE)}")
    print(f"Search-form-only (disable): {len(SEARCH_FORM_ONLY)}")
    print(f"No roster (disable): {len(NO_ROSTER)}")
    
    # Generate SQL
    sql = []
    
    # 1. Switch GovernmentWebsite jurisdictions to gov_website_staging
    for state, county in GOV_WEBSITE:
        sql.append(f"UPDATE records.jurisdictions SET adapter='gov_website_staging', staging_only=true, enabled=false WHERE state='{state}' AND county='{county}' AND adapter='html_roster_staging';")
    
    # 2. Disable search-form-only
    for state, county in SEARCH_FORM_ONLY:
        sql.append(f"UPDATE records.jurisdictions SET enabled=false WHERE state='{state}' AND county='{county}' AND adapter='html_roster_staging';")
    
    # 3. Disable no-roster
    for state, county in NO_ROSTER:
        sql.append(f"UPDATE records.jurisdictions SET enabled=false WHERE state='{state}' AND county='{county}' AND adapter='html_roster_staging';")
    
    # 4. Enable table-roster ones (they're already enabled, but make sure)
    for state, county in TABLE_ROSTER:
        sql.append(f"UPDATE records.jurisdictions SET enabled=true, staging_only=false WHERE state='{state}' AND county='{county}' AND adapter='html_roster_staging';")
    
    print(f"\n=== SQL TO EXECUTE ({len(sql)} statements) ===")
    for s in sql:
        print(s)
    
    return sql


if __name__ == '__main__':
    main()
