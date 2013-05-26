import requests


def scrape():
    r = requests.Session()
    results = r.post(
        "http://cia.china-airlines.com/LoginHandler",
        params={'userid': '635426',
                'password': 'ju635426'}
    )
    # print results.text

    # results = r.post(
    #     "http://cia.china-airlines.com/cia_rpt_roster_summary.jsp",
    #     params={'userid': '635426',
    #             'password': 'ju635426'}
    # )
    # print results.text

    # results = r.post(
    #     "http://cia.china-airlines.com/cia_inq_view_rostsummary.jsp",
    #     params={'staffNum': '635426',
    #             'rosterPeriod': '01May2013 - 31May2013',
    #             'display_timezone': 'Port Local'
    #     }
    # )
    # print results.text

    results = r.post(
        "http://cia.china-airlines.com/cia_inq_view_rostreport.jsp",
        params={'staffNum': '635426',
                'strDay': '01',
                'strMonth': '05',
                'strYear': '2013',
                'endDay': '31',
                'endMonth': '05',
                'endYear': '2013',
                'display_timezone': 'Port Local'
        }
    )
    print results.text

if __name__ == "__main__":
    scrape()
