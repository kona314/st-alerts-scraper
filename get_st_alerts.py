import requests, os
from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Optional 

all_routes = ["1 Line", "T Line", "N Line", "S Line", "510", "511", "512", "513", "522", "532", "535", "540", "542", "545", "550", "554", "555", "556", "560", "566", "567", "574", "577", "578", "580", "586", "590", "592", "594", "595", "596"]
date_format = "%b %d - %I:%M %p"
labels_to_gtfsrt_effect = {"Reroute": "DETOUR", "Stop closure": "DETOUR", "Elevator outage": "ACCESSIBILITY_ISSUE"}

## Supply a filename to use stored HTML. Helpful for debugging.
cache_file = os.environ.get('ST_ALERTS_CACHE_FILE')

class STAlert:
    def __init__(self, title: str, body: str, routes: List[str], posted: datetime, updated: Optional[datetime], url: Optional[str], effect: Optional[str]):
        self.title = title
        self.body = body
        self.routes = routes
        self.posted = posted
        self.updated = updated
        self.url = url 
        self.effect = effect 

def get_st_alerts() -> List[STAlert]:
    alerts = []
    now = datetime.now()
    seen_titles = set()

    text = ""

    if cache_file is not None:
        with open(cache_file) as file:
            text = file.read()
    else:
        url = "https://www.soundtransit.org/ride-with-us/service-alerts"
        page = requests.get(url)
        text = page.text 
    
    parsed = BeautifulSoup(text, 'html.parser')

    alerts_els = parsed.find_all(class_="alert__body")

    for el in alerts_els:
        main_section = el.find(class_="alert__body--main")
        title = main_section.contents[1].text.strip()
        if title in seen_titles:
            continue 
        else: 
            seen_titles.add(title)
        routes = main_section.contents[3].text.strip() if len(main_section.contents) > 3 else None 
        if not routes: 
            continue

        routes = routes.replace("Routes ", "")
        routes = routes.replace("Route ", "")
        
        url_el = main_section.find("a")
        url = None 
        if url_el:
            url = "https://www.soundtransit.org" + url_el.attrs['href']
        
        dates = el.find(class_="alert__body--section")
        
        body = el.find(class_="acc__panel alert__body--section")
        body = body.get_text().strip().replace("\n", "\n\n")
        
        label = el.find(class_="alert--label")
        effect = None 
        if label and label.text.strip() in labels_to_gtfsrt_effect:
            effect = labels_to_gtfsrt_effect[label.text.strip()]
        
        dates = list(dates.children)
        posted = dates[0].text.strip() 
        posted = posted.replace(".", "")
        updated = dates[1].text.strip() if len(dates) > 1 else None 
        if updated:
            updated = updated[10 : -1]
            updated = updated.replace(".", "")
            updated = datetime.strptime(updated, date_format)
            updated = updated.replace(year=now.year)
            if updated > now:
                updated = updated.replace(year=now.year - 1)
        posted = datetime.strptime(posted, date_format)
        posted = posted.replace(year=now.year)
        if posted > now:
            posted = posted.replace(year=now.year - 1)

        routes_found = []
        for route in all_routes:
            if route in routes:
                routes_found.append(route)

        alert = STAlert(title, body, routes_found, posted, updated, url, effect)
        alerts.append(alert)

    return alerts