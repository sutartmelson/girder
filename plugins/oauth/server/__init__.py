#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

from girder import events
from girder.constants import SettingDefault, SortDir
from girder.models.model_base import ModelImporter, ValidationException
from . import rest, constants, providers


def validateSettings(event):
    key, val = event.info['key'], event.info['value']

    if key == constants.PluginSettings.PROVIDERS_ENABLED:
        if not isinstance(val, (list, tuple)):
            raise ValidationException('The enabled providers must be a list.',
                                      'value')
        event.preventDefault().stopPropagation()
    elif key in (constants.PluginSettings.GOOGLE_CLIENT_ID,
                 constants.PluginSettings.GITHUB_CLIENT_ID,
                 constants.PluginSettings.LINKEDIN_CLIENT_ID,
                 constants.PluginSettings.BITBUCKET_CLIENT_ID,
                 constants.PluginSettings.GOOGLE_CLIENT_SECRET,
                 constants.PluginSettings.GITHUB_CLIENT_SECRET,
                 constants.PluginSettings.LINKEDIN_CLIENT_SECRET,
                 constants.PluginSettings.BITBUCKET_CLIENT_SECRET,
                 constants.PluginSettings.GOOGLE_WHITELIST,
                 constants.PluginSettings.GITHUB_WHITELIST,
                 constants.PluginSettings.LINKEDIN_WHITELIST,
                 constants.PluginSettings.BITBUCKET_WHITELIST,):
        event.preventDefault().stopPropagation()


def checkOauthUser(event):
    """
    If an OAuth2 user without a password tries to log in with a password, we
    want to give them a useful error message.
    """
    user = event.info['user']
    if user.get('oauth'):
        if isinstance(user['oauth'], dict):
            # Handle a legacy format where only 1 provider (Google) was stored
            prettyProviderNames = 'Google'
        else:
            prettyProviderNames = ', '.join(
                providers.idMap[val['provider']].getProviderName(external=True)
                for val in user['oauth']
            )
        raise ValidationException(
            'You don\'t have a password. Please log in with %s, or use the '
            'password reset link.' % prettyProviderNames)


def load(info):
    ModelImporter.model('user').ensureIndex((
        (('oauth.provider', SortDir.ASCENDING),
         ('oauth.id', SortDir.ASCENDING)), {}))
    ModelImporter.model('user').reconnect()

    events.bind('model.setting.validate', 'oauth', validateSettings)
    events.bind('no_password_login_attempt', 'oauth', checkOauthUser)

    info['apiRoot'].oauth = rest.OAuth()

    # Make Google on by default for backward compatibility. To turn it off,
    # users will need to hit one of the "Save" buttons on the config page.
    SettingDefault.defaults[constants.PluginSettings.PROVIDERS_ENABLED] = \
        ['google']
