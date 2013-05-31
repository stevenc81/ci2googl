#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2


import httplib2
import logging
import os
import pickle
import requests

from apiclient.discovery import build
from oauth2client.appengine import oauth2decorator_from_clientsecrets
from oauth2client.client import AccessTokenRefreshError
from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
import re
from datetime import datetime, date
from datetime import timedelta
from BeautifulSoup import BeautifulSoup
from calendar import monthrange
from google.appengine.api import urlfetch


# CLIENT_SECRETS, name of a file containing the OAuth 2.0 information for this
# application, including client_id and client_secret, which are found
# on the API Access tab on the Google APIs
# Console <http://code.google.com/apis/console>
CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets.json')

# Helpful message to display in the browser if the CLIENT_SECRETS file
# is missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
<h1>Warning: Please configure OAuth 2.0</h1>
<p>
To make this sample run you will need to populate the client_secrets.json file
found at:
</p>
<p>
<code>%s</code>.
</p>
<p>with information found on the <a
href="https://code.google.com/apis/console">APIs Console</a>.
</p>
""" % CLIENT_SECRETS


http = httplib2.Http(memcache)
service = build("calendar", "v3", http=http)
decorator = oauth2decorator_from_clientsecrets(
    CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/calendar',
    message=MISSING_CLIENT_SECRETS_MESSAGE)


def _nbsp_trim(string):
    return str(string.replace('&nbsp;', ''))


def _create_event(service, http, summary, dt, edt, location='TPE'):

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

    created_event = service.events().insert(calendarId='primary', body=event).execute(http=http)
    return created_event['summary']


class MainHandler(webapp2.RequestHandler):

    @decorator.oauth_aware
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'grant.html')
        variables = {
            'url': decorator.authorize_url(),
            'has_credentials': decorator.has_credentials()
        }
        self.response.out.write(template.render(path, variables))


class ImportHandler(webapp2.RequestHandler):

    @decorator.oauth_required
    def get(self):
        try:
            # http = decorator.http()
            # text =  service.calendars().get(calendarId='primary').execute(http=http)['summary']
          # created = cal_import(service)
          # user = service.people().get(userId='me').execute(http=http)
          # text = 'Hello, %s!' % user['displayName']

            # path = os.path.join(os.path.dirname(__file__), 'welcome.html')
            # self.response.out.write(template.render(path, {'text': text }))
            self.response.out.write('''
                <html>
                  <body>
                    <form method="post">
                        <p>Crew ID: <input type="text" name="crew_id" /></p>
                        <p>Month: <input type="month" name="month" /></p>
                        <p><input type="submit" value="Import" /></p>
                    </form>
                  </body>
                </html>
        ''')
        except AccessTokenRefreshError:
            self.redirect('/')

    @decorator.oauth_required
    def post(self):
        urlfetch.set_default_fetch_deadline(30)

        crew_id = str(self.request.get('crew_id'))
        month = str(self.request.get('month').split('-')[1])
        year = str(self.request.get('month').split('-')[0])
        strDay, endDay = monthrange(2013, int(month))
        endDay = str(endDay)

        queryStartDate = datetime.strptime(year + month + '01', '%Y%m%d')
        queryEndDate = datetime.strptime(year + month + str(endDay), '%Y%m%d')

        http = decorator.http()
        event_list = service.events().list(
            calendarId='primary',
            maxResults='9999',
            timeMin=queryStartDate.strftime('%Y-%m-%d')
            + 'T'
            + '00:00:00'
            + '.000+08:00',
            timeMax=queryEndDate.strftime('%Y-%m-%d')
            + 'T'
            + '23:59:59'
            + '.000+08:00').execute(http=http)

        deleted_events = []
        if 'items' in event_list:
            for each_event in event_list['items']:
                if each_event['summary'].startswith('CI') or each_event['summary'].startswith('STDBY') or each_event['summary'].startswith('AE'):
                    service.events().delete(
                        calendarId='primary',
                        eventId=each_event['iCalUID'].replace('@google.com', '')).execute(http=http)
                    deleted_events.append(each_event['summary'])

        r = requests.Session()
        results = r.post(
            "http://cia.china-airlines.com/LoginHandler",
            data={
                'userid': '635426',
                'password': '$1688$'}
        )

        results = r.post(
            "http://cia.china-airlines.com/cia_inq_view_rostreport.jsp",
            data={
                'staffNum': crew_id,
                'strDay': '01',
                'strMonth': month,
                'strYear': year,
                'endDay': endDay,
                'endMonth': month,
                'endYear': year,
                'display_timezone': 'Port Local'}
        )

        soup = BeautifulSoup(results.text)

        r.get("http://cia.china-airlines.com/cia_gen_logoff.jsp")

        created_events = []
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
                        event = _create_event(
                            service,
                            http,
                            orig_flight_number,
                            datetime.strptime(orig_signin_date + orig_signin, '%d%b%y%H%M'),
                            datetime.strptime(current_date + eta, '%d%b%y%H%M'),
                            destination)
                        created_events.append(event)
            if re.search(r'^S[1-6|B]$', duty) is not None:
                event = _create_event(
                    service,
                    http,
                    flight_number,
                    datetime.strptime(current_date + signin, '%d%b%y%H%M'),
                    datetime.strptime(current_date + eta, '%d%b%y%H%M'))

                created_events.append(event)

        if on_duty:
            event = _create_event(
                service,
                http,
                orig_flight_number,
                datetime.strptime(orig_signin_date + orig_signin, '%d%b%y%H%M'),
                datetime.strptime(current_date + eta, '%d%b%y%H%M'))
            created_events.append(event)

        self.response.out.write('Deleted: ' + str(deleted_events) + '<br>' + 'Added: ' + str(created_events))


app = webapp2.WSGIApplication(
    [
    ('/', MainHandler),
    ('/import', ImportHandler),
    (decorator.callback_path, decorator.callback_handler()),
    ],
    debug=True)
run_wsgi_app(app)