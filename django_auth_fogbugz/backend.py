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
    _server_validator = URLValidator(message=
        "AUTH_FOGBUGZ_SERVER must be set to a valid fogbugz api url.")
    
    defaults = dict(
    #   SETTING_NAME         =     ('Default Value', Validator),
        SERVER               =     (None,            _server_validator),
        ENABLE_PROFILE       =     (False,           None),
        ENABLE_PROFILE_TOKEN =     (False,           None),
        ALLOW_COMMUNITY      =     (False,           None),
        AUTO_CREATE_USERS    =     (False,           None),
        SERVER_USES_LDAP     =     (False,           None),
        MAP_ADMIN_AS_SUPER   =     (False,           None),
        MAP_ADMIN_AS_STAFF   =     (False,           None),
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
    
def _username_from_email(email):
    return email.lower()

class NullHandler(logging.Handler):
    def emit(self, record):
        pass

logger = logging.getLogger('django_auth_fogbugz')
logger.addHandler(NullHandler())
            
class FogBugzBackend(ModelBackend):
    
    def authenticate(self, username=None, password=None):
        if not username or not password:
            return None
        
        ## FogBugz does case insensitive matching. We lower-case the input
        ## and then do an insensitive match on the e-mail field.
        ## This will allow for hand created accounts, and for when
        ## LDAP is enabled.
        username = username.lower()
        
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
                email_login = True
                user = UserModel.objects.get(email__iexact=username)
            elif '\\' in username:
                ## LDAP username with domain specified, strip the '\\'
                username = username.split('\\')[-1]
                user = UserModel.objects.get_by_natural_key(username)
            else:
                user = UserModel.objects.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            logger.debug("No pre-existing user model for user (%s).", username)
                
        if not user and not fbcfg.AUTO_CREATE_USERS:
            ## no existing user, and not allowed to create new ones
            logger.debug(
                "Login Failed: No auto creation of users, "
                "login failed for user (%s).", username)
            return None

        if not email_login and not fbcfg.SERVER_USES_LDAP:
            ## Reguardless if it is an existing user, if we do not have
            ## SERVER_USES_LDAP set then we must require an e-mail login.
            ## If this is a non-FogBugz login, then a later backend
            ## will do the authentication for it.
            logger.debug("Login Failed: User (%s) logged in with non-e-mail "
                         "username and AUTH_FOGBUGZ_SERVER_USES_LDAP "
                         "is not set. ", username)
            return None
        
        if not user and email_login and fbcfg.SERVER_USES_LDAP:
            ## no existing user, and logging in with e-mail, but
            ## fogbugz has LDAP integration allowing for logging in
            ## with both e-mail and ldap name. Because of this, we only
            ## allow creating the user account when logging in with the
            ## LDAP username, not the e-mail. Once a person logs in with
            ## the LDAP username, they can authenticate with the e-mail
            ## address.
            logger.debug("Login Failed: User logged in for the first time "
                         "with an e-mail address (%s), but the FogBugz server "
                         "(%s) is configured for LDAP authentication. User "
                         "must login with their LDAP username the "
                         "first time. ", username, fbcfg.SERVER)
            return None
        


        try:
            fb = fogbugz.FogBugz(fbcfg.SERVER)
        except fogbugz.FogBugzConnectionError, e:
            ## Log the error
            logger.error("Login Failed: "
                         "FogBugz Server (%s) Connection Error: %s",
                         fbcfg.SERVER, e.message)
            return None
        
        if user and fbcfg.ENABLE_PROFILE:
            ## get the old token from the profile
            token = None
            try:
                token = user.fogbugzprofile.token
                ixPerson = user.fogbugzprofile.ixPerson
            except FogBugzProfile.DoesNotExist:
                logger.debug("No existing token for user (%s).", username)
            if token:
                logger.debug("Clearing existing token for user (%s).",username)
                fb.token(token)
                try:
                    ## Loging off explicitly will clear the token
                    fb.logoff()
                except Exception, e:
                    ## reset it if the logoff failed. Could fail for many
                    ## reasons. Later logon logic will handle meaningful
                    ## errors.
                    logger.warning("Failed to clear old token for user (%s). "
                                   "Reconnecting to FogBugz Server (%s). "
                                   "Message: %s",
                                   username, fbcfg.SERVER, str(e))
                    fb = fogbugz.FogBugz(fbcfg.SERVER)

        try:
            fb.logon(username, password)
        except fogbugz.FogBugzLogonError, e:
            ## Log:
            logger.debug("Login Failed: "
                "Authentication Failure on Server (%s) for user (%s): %s",
                fbcfg.SERVER, username, str(e))
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
        community = fbPerson.fcommunity.string=='true'
        if not fbcfg.ALLOW_COMMUNITY and community:
            ## Log:
            logger.debug("Login Failed: Community users are not allowed. "
                         "User (%s) is a community user on Server (%s).",
                         username, fbcfg.SERVER)
            try:
                fb.logoff()
            except Exception, e:
                logger.warning("Failed to logoff community user (%s) from "
                               "server (%s): %s", username, fbcfg.SERVER,
                               str(e))
            return None
        
        if not ixPerson:
            ixPerson = int(fbPerson.ixperson.string,10)
        fullname = fbPerson.sfullname.string
        admin = fbPerson.fadministrator.string == 'true'
        verb1 = 'Removing'
        verb2 = 'from'
        if admin:
            verb1 = 'Adding'
            verb2 = 'to'
            
        if user:
            changed_user = False
            if fbcfg.MAP_ADMIN_AS_SUPER:
                if user.is_superuser != admin:
                    user.is_superuser = admin
                    changed_user = True
                    logger.debug("%s superuser access %s user (%s) from "
                                 "server (%s).", verb1, verb2,
                                 username, fbcfg.SERVER)
            if admin and fbcfg.MAP_ADMIN_AS_STAFF:
                if user.is_staff != admin:
                    user.is_staff = admin
                    logger.debug("%s staff access %s user (%s) from "
                                 "server (%s).", verb1, verb2,
                                 username, fbcfg.SERVER)
                    changed_user = True
            if changed_user:
                user.save()

            if fbcfg.ENABLE_PROFILE:
                try:
                    if fbcfg.ENABLE_PROFILE_TOKEN:
                        user.fogbugzprofile.token = fb._token
                    user.fogbugzprofile.is_normal = not community and not admin
                    user.fogbugzprofile.is_community = community
                    user.fogbugzprofile.is_administrator = admin
                    user.fogbugzprofile.save()
                    logger.debug("Updated user (%s) token for server (%s).",
                                 username, fbcfg.SERVER)
                except FogBugzProfile.DoesNotExist:
                    token = ''
                    if fbcfg.ENABLE_PROFILE_TOKEN:
                        token = fb._token
                    fbprofile = FogBugzProfile(
                        user = user,
                        is_normal = not community and not admin,
                        is_community = community,
                        is_administrator = admin,
                        ixPerson = ixPerson,
                        token = token)
                    logger.debug("Created user (%s) token profile for "
                                 "server (%s).", username, fbcfg.SERVER)
                    fbprofile.save()
            
            
            if not fbcfg.ENABLE_PROFILE_TOKEN or not fbcfg.ENABLE_PROFILE:
                ## clear the token, as we are not saving it.
                try:
                    fb.logoff()
                except Exception, e:
                    logger.warning("Failed to logoff user (%s) from "
                                   "server (%s): %s", username, fbcfg.SERVER,
                                   str(e))
                
            return user
        
        ## Create a new user and profile and return it.
        if email_login:
            email = username
            username = _username_from_email(email)
        else:
            email = fbPerson.semail.string
        
        logger.debug("Creating new user with token profile for "
                     "user (%s) from server (%s).", username, fbcfg.SERVER)
        
        user = UserModel.objects.create_user(username=username, email=email)
        user.first_name = fullname
        if admin and fbcfg.MAP_ADMIN_AS_SUPER:
            logger.debug("%s superuser access %s user (%s) from "
                         "server (%s).", verb1, verb2, username, fbcfg.SERVER)
            user.is_superuser = True
        if admin and fbcfg.MAP_ADMIN_AS_STAFF:
            logger.debug("%s staff access %s user (%s) from "
                         "server (%s).", verb1, verb2, username, fbcfg.SERVER)
            user.is_staff = True
        user.save()
        if fbcfg.ENABLE_PROFILE:
            token = ''
            if fbcfg.ENABLE_PROFILE_TOKEN:
                token = fb._token
            fbprofile = FogBugzProfile(
                user = user,
                ixPerson = ixPerson,
                is_normal = not community and not admin,
                is_community = community,
                is_administrator = admin,
                token = token)
            fbprofile.save()
        
        if not fbcfg.ENABLE_PROFILE_TOKEN or not fbcfg.ENABLE_PROFILE:
            ## clear the token as we are not saving it
            try:
                fb.logoff()
            except Exception, e:
                logger.warning("Failed to logoff user (%s) from "
                               "server (%s): %s", username, fbcfg.SERVER,
                               str(e))

        return user
