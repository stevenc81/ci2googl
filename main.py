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
                        <p>Crew ID: <input type="text name="crew_id" /></p>
                        <p><input type="submit" value="Submit" /></p>
                    </form>
                  </body>
                </html>
        ''')
        except AccessTokenRefreshError:
            self.redirect('/')

    @decorator.oauth_required
    def post(self):
        crew_id = self.request.get('crew_id')

        r = requests.Session()
        results = r.post(
            "http://cia.china-airlines.com/LoginHandler",
            params={'userid': '635426',
                    'password': 'ju635426'}
        )

        results = r.post(
            "http://cia.china-airlines.com/cia_inq_view_rostreport.jsp",
            params={'staffNum': '635426',
                    'strDay': '01',
                    'strMonth': '05',
                    'strYear': '2013',
                    'endDay': '31',
                    'endMonth': '05',
                    'endYear': '2013',
                    'display_timezone': 'Port Local'}
        )

        # event = {
        #     'summary': 'Appointment',
        #     'location': 'Somewhere',
        #     'start': {
        #         'dateTime': '2013-06-25T10:00:00.000-07:00'
        #     },
        #     'end': {
        #         'dateTime': '2013-06-25T10:25:00.000-07:00'
        #     }
        # }
        # http = decorator.http()
        # request = service.events().insert(calendarId='primary', body=event).execute(http=http)
        self.response.out.write(results.text)

app = webapp2.WSGIApplication(
    [
    ('/', MainHandler),
    ('/import', ImportHandler),
    (decorator.callback_path, decorator.callback_handler()),
    ],
    debug=True)
run_wsgi_app(app)