import requests
import re
import json
from datetime import datetime
from BeautifulSoup import BeautifulSoup
from calendar import monthrange


def _nbsp_trim(string):
    return str(string.replace('&nbsp;', ''))


def _create_event(summary, dt, edt, location='TPE'):

    event = {
        'summary': summary,
        'location': location,
        'start': {
            'dateTime': dt.strftime('%Y-%m-%d')
            + 'T'
            + dt.strftime('%H:%M:%S')
            + '.000+08:00'
        },
        'end': {
            'dateTime': edt.strftime('%Y-%m-%d')
            + 'T'
            + edt.strftime('%H:%M:%S')
            + '.000+08:00'
        },
        'attendees': [
        ]
    }
    print event
    return event


def scrape():
    year_month = '2013-05'
    month = str(year_month.split('-')[1])
    year = str(year_month.split('-')[0])
    strDay, endDay = monthrange(int(year), int(month))

    with open('ci_credentials.json') as f:
        cred = json.load(f)

    r = requests.Session()
    results = r.post(
        "http://cia.china-airlines.com/LoginHandler",
        data={'userid': cred['userid'],
        'password': cred['password']}
    )

    results = r.post(
        "http://cia.china-airlines.com/cia_inq_view_rostreport.jsp",
        data={'staffNum': '635426',
        'strDay': '01',
        'strMonth': month,
        'strYear': year,
        'endDay': endDay,
        'endMonth': month,
        'endYear': year,
        'display_timezone': ' Port Local'}
    )
    r.get("http://cia.china-airlines.com/cia_gen_logoff.jsp")

    soup = BeautifulSoup(results.text)
    on_duty = False
    for row in soup('tr'):
        cols = row('td')
        if len(cols) != 12:
            continue

        date = _nbsp_trim(cols[0].text)
        duty = _nbsp_trim(cols[2].text)
        sector = _nbsp_trim(cols[8].text)
        eta = _nbsp_trim(cols[9].text)
        signin = _nbsp_trim(cols[6].text)
        etd = _nbsp_trim(cols[7].text)
        flight_number = _nbsp_trim(cols[4].text)

        if re.search(r'^\d+\w+\d+$', date) is not None:
            current_date = date

        if on_duty is False:
            if sector.startswith('TPE') is True and sector.endswith('TPE') is False:
                destination = sector[-3:]
                orig_signin = signin if signin != '' else etd
                orig_signin_date = current_date if date == '' else date
                orig_flight_number = flight_number
                on_duty = True
        else:
            if sector.startswith('TPE') is False and sector.endswith('TPE') is True:
                if eta != '2359':
                    on_duty = False
                    dt = datetime.strptime(orig_signin_date + orig_signin, '%d%b%y%H%M')
                    edt = datetime.strptime(current_date + eta, '%d%b%y%H%M')
                    _create_event(orig_flight_number, dt, edt, destination)

        if re.search(r'^S[1-6|B]$', duty) is not None:
            dt = datetime.strptime(current_date + signin, '%d%b%y%H%M')
            edt = datetime.strptime(current_date + eta, '%d%b%y%H%M')

            _create_event(flight_number, dt, edt)

    if on_duty:
        dt = datetime.strptime(orig_signin_date + orig_signin, '%d%b%y%H%M')
        edt = datetime.strptime(current_date + eta, '%d%b%y%H%M')
        _create_event(orig_flight_number, dt, edt, destination)

if __name__ == "__main__":
    scrape()
