import requests
import re
from datetime import datetime
from BeautifulSoup import BeautifulSoup
from datetime import timedelta
from calendar import monthrange


def _nbsp_trim(string):
    return string.replace('&nbsp;', '')


def scrape():
    month = '2013-06'
    month = month.split('-')[1]
    strDay, endDay = monthrange(2013, int(month))

    r = requests.Session()
    results = r.post(
        "http://cia.china-airlines.com/LoginHandler",
        params={'userid': '635426',
                'password': '$1688$'}
    )

    results = r.post(
        "http://cia.china-airlines.com/cia_inq_view_rostreport.jsp",
        params={'staffNum': '635426',
                'strDay': '01',
                'strMonth': month,
                'strYear': '2013',
                'endDay': endDay,
                'endMonth': month,
                'endYear': '2013',
                'display_timezone': 'Port Local'}
    )
    # print results.text

    # f = open('req_result.html', 'w')
    # f.write(results.text)
    # f.close()

    # f = open('sample.html')
    soup = BeautifulSoup(results.text)
    # f.close()

    fly_date = ''
    for row in soup('tr'):
        cols = row('td')
        if len(cols) != 12:
            continue
        if re.search(r'^\d+\w+\d+&nbsp;$', cols[0].text) is not None:
            fly_date = _nbsp_trim(cols[0].text)
        if cols[2].text.find('FLY') != -1 and cols[6].text != '&nbsp;':
            fly_time = _nbsp_trim(cols[6].text)
            fly_summary = _nbsp_trim(cols[4].text)

            dt = datetime.strptime(fly_date + fly_time, '%d%b%y%H%M')
            edt = dt + timedelta(hours=8)

            event = {
                'summary': str(fly_summary),
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

if __name__ == "__main__":
    scrape()
