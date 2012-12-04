# Copyright (c) 2012, Douglas Napoleone.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright notice,
#        this list of conditions and the following disclaimer.
#     
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
# 
#     3. Neither the name of Django nor the names of its contributors may be
#        used to endorse or promote products derived from this software without
#        specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from django.contrib.auth.backends import ModelBackend
from django.core.validators import URLValidator, email_re

try:
    from django.contrib.auth import get_user_model
except ImportError:
    from django.contrib.auth.models import User
    def get_user_model():
        return User
    
import sys
import traceback
import logging

import fogbugz

from models import FogBugzProfile

class FogBugzSettings(object):
    """
    Django setting wrapper, ensuring all values exist with defaults.
    """
    _server_validator = URLValidator(
        "AUTH_FOGBUGZ_SERVER must be set to a valid fogbugz api url.")
    
    defaults = dict(
    #   SETTING_NAME        =     ('Default Value', Validator)
        SERVER              =     (None,            _server_validator),
        ENABLE_TOKEN_PROFILE=     (False,           None),
        ALLOW_COMMUNITY     =     (False,           None),
        AUTO_CREATE_USERS   =     (False,           None),
        SERVER_USES_LDAP    =     (False,           None),
        MAP_ADMIN_AS_SUPER  =     (False,           None),
        MAP_ADMIN_AS_STAFF  =     (False,           None),
    )

    def __init__(self, prefix='AUTH_FOGBUGZ_'):
        """
        Loads our settings from django.conf.settings, applying defaults,
        and raising an exception if a validator is supplied and fails.
        """
        from django.conf import settings

        for name, (default, test) in self.defaults.iteritems():                
            value = getattr(settings, prefix + name, default)

            if callable(test):
                test(value)

            setattr(self, name, value)

def _free_token(fb, token):
    current = fb._token
    if current:
        fb._token = None
    fb.token(token)
    try:
        #### RED_FLAG: Log stuff
        ## Log clearing token (but not the actual token string)
        fb.logoff()
    except:
        ## reset it if the logoff failed. Could fail for many reasons.
        ## Later logon logic will handle meaningful errors.
        fb = fogbugz.FogBugz(fbcfg.SERVER)
    fb.token(current)
    
def _username_from_email(email):
    return email

class NullHandler(logging.Handler):
    def emit(self, record):
        pass

logger = logging.getLogger('django_auth_fogbugz')
logger.addHandler(NullHandler())
            
class FogBugzBackend(ModelBackend):
    
    def authenticate(self, username=None, password=None):
        if not username or not password:
            return None
        
        fbcfg = FogBugzSettings()
                
        ## first check to see if there is already a user account for this
        ## user.
        user = None
        email = ''
        ixPerson = 0
        email_login = False
        
        UserModel = get_user_model()
        ## the problem here is that it could be the email address
        ## or an LDAP user login.
        try:
            if email_re.search(username):
                ## it's an e-mail address...
                user = UserModel.objects.get(email=username)
                email_login = True
            elif '\\' in username:
                ## LDAP username with domain specified, strip the '\\'
                username = username.split('\\')[-1]
                user = UserModel.objects.get_by_natural_key(username)
            else:
                user = UserModel.objects.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            logger.debug
                
        if not user and not fbcfg.AUTO_CREATE_USERS:
            ## no existing user, and not allowed to create new ones
            logger.debug
            return None
        
        if not user and email_login and fbcfg.SERVER_USES_LDAP:
            ## no existing user, and logging in with e-mail, but
            ## fogbugz has LDAP integration allowing for logging in
            ## with both e-mail and ldap name. Because of this, we only
            ## allow creating the user account when logging in with the
            ## LDAP username, not the e-mail. Once a person logs in with
            ## the LDAP username, they can authenticate with the e-mail
            ## address.
            logger.debug
            return None

        try:
            fb = fogbugz.FogBugz(fbcfg.SERVER)
        except fogbugz.FogBugzConnectionError, e:
            ## Log the error
            logger.error
            fbcfg.SERVER, e.message
            return None
        
        if user and fbcfg.ENABLE_TOKEN_PROFILE:
            ## get the old token from the profile
            token = None
            try:
                token = user.fogbugzprofile.token
                ixPerson = user.fogbugzprofile.ixPerson
            except FogBugzProfile.DoesNotExist:
                logger.debug
            if token:
                logger.debug            
                _free_token(fb, token)

        try:
            fb.logon(username, password)
        except fogbugz.FogBugzLogonError, e:
            ## Log:
            logger.debug
            fbcfg.SERVER, username, e.message
            #### RED_FLAG: check for inactive user and set in Django if there
            ####           is a Django user.
            
            return None
            
        ## NOTE: FogBugz allows for logging in with the e-mail address
        ##       as well as the username. Make sure you have the proper
        ##       username.
        ## We also do not want to allow community users unless settings
        ## says we should.
        res = fb.viewPerson()
        fbPerson=res.person
        if not fbcfg.ALLOW_COMMUNITY and fbPerson.fcommunity.string=='true':
            ## Log:
            fbcfg.SERVER, e.username, "Community users are not allowed."
            return None
        
        if not ixPerson:
            ixPerson = int(fbPerson.ixperson.string,10)
        fullname = fbPerson.sfullname.string
        admin = fbPerson.fadministrator.string == 'true'
        
        if user:
            changed_user = False
            if fbcfg.MAP_ADMIN_AS_SUPER:
                if user.is_superuser != admin:
                    user.is_superuser = admin
                    changed_user = True
                    logger.debug
            if admin and fbcfg.MAP_ADMIN_AS_STAFF:
                if user.is_staff != admin:
                    user.is_staff = admin
                    logger.debug
                    changed_user = True
            if changed_user:
                user.save()

            if fbcfg.ENABLE_TOKEN_PROFILE:
                try:    
                    user.fogbugzprofile.token = fb._token
                    user.fogbugzprofile.save()
                    logger.debug
                    #log update
                except FogBugzProfile.DoesNotExist:
                    fbprofile = FogBugzProfile(
                        user = user,
                        ixPerson = ixPerson,
                        token = fb._token)
                    logger.debug
                    fbprofile.save()
                
            return user
        
        ## Create a new user and profile and return it.
        if email_login:
            email = username
            username = _username_from_email(email)
        else:
            email = fbPerson.semail.string
        
        logger.debug
        
        user = UserModel.objects.create_user(username=username, email=email)
        user.first_name = fullname
        if admin and fbcfg.MAP_ADMIN_AS_SUPER:
            user.is_superuser = True
        if admin and fbcfg.MAP_ADMIN_AS_STAFF:
            user.is_staff = True
        user.save()
        if fbcfg.ENABLE_TOKEN_PROFILE:
            fbprofile = FogBugzProfile(
                user = user,
                ixPerson = ixPerson,
                token = fb._token)
            fbprofile.save()

        return user
