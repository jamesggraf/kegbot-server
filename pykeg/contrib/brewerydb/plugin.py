# Copyright 2014 Bevbot LLC, All Rights Reserved
#
# This file is part of the Pykeg package of the Kegbot project.
# For more information on Pykeg or Kegbot, see http://kegbot.org/
#
# Pykeg is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# Pykeg is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pykeg.  If not, see <http://www.gnu.org/licenses/>.

"""BreweryDB plugin for Kegbot."""

from django.conf import settings
from pykeg.plugin import plugin

from . import forms
from . import views

KEY_SITE_SETTINGS = 'settings'
KEY_CLIENT_SECRET = 'client_secret'

class BreweryDbPlugin(plugin.Plugin):
    NAME = 'Brewery DB'
    SHORT_NAME = 'brewerydb'
    DESCRIPTION = 'Lookup beers with BreweryDB!'
    URL = 'http://kegbot.org'
    VERSION = '0.0.1-pre'
    BREWERY_DB_API_ROOT = 'http://api.brewerydb.com/v2/'
    BREWERY_DB_API_SEARCH = BREWERY_DB_API_ROOT + 'search'

    def get_admin_settings_view(self):
        if settings.EMBEDDED:
            return None
        return views.admin_settings

    def get_user_settings_view(self):
        pass

    def get_extra_user_views(self):
        return []

    def handle_new_events(self, events):
        for event in events:
            self.handle_event(event)

    def handle_event(self, event):
        self.logger.info('Handling new event: %s' % event)
        user = event.user

        if user.is_guest():
            self.logger.info('Ignoring event: anonymous.')
            return

        self.logger.info('Handled event: %s' % event)


    ### Brewery-db-specific methods

    def get_credentials(self):
        if settings.EMBEDDED:
            return (
                getattr(settings, 'BREWERYDB_CLIENT_SECRET', ''),
            )
        data = self.get_site_settings()
        return data.get('client_secret')

    def get_site_settings_form(self):
        return self.datastore.load_form(forms.SiteSettingsForm, KEY_SITE_SETTINGS)

    def get_site_settings(self):
        return self.get_site_settings_form().initial

    def save_site_settings_form(self, form):
        self.datastore.save_form(form, KEY_SITE_SETTINGS)
