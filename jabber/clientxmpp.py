'''
Created on 26 Jan 2013

@author: Rubin
'''

import sleekxmpp
from sleekxmpp.exceptions import IqError, IqTimeout

class AutoRegisterClientXMPP(sleekxmpp.ClientXMPP):

    def __init__(self, jid, password):
        super(AutoRegisterClientXMPP, self).__init__(jid, password)
        self.add_event_handler("register", self.register)
        self.add_event_handler("ssl_invalid_cert", self.ssl_invalid_cert)

        #self.register_plugin('xep_0030') # Service Discovery
        #self.register_plugin('xep_0004') # Data forms
        #self.register_plugin('xep_0066') # Out-of-band Data
        self.register_plugin('xep_0077') # In-band Registration
        
    def register(self, iq):
        """
        Fill out and submit a registration form.

        The form may be composed of basic registration fields, a data form,
        an out-of-band link, or any combination thereof. Data forms and OOB
        links can be checked for as so:

        if iq.match('iq/register/form'):
            # do stuff with data form
            # iq['register']['form']['fields']
        if iq.match('iq/register/oob'):
            # do stuff with OOB URL
            # iq['register']['oob']['url']

        To get the list of basic registration fields, you can use:
            iq['register']['fields']
        """
        resp = self.Iq()
        resp['type'] = 'set'
        resp['register']['username'] = self.boundjid.user
        resp['register']['password'] = self.password

        try:
            resp.send(now=True)
            print "Account created for %s!" % self.boundjid
        except IqError as e:
            print "Could not register account %s: %s" % (self.boundjid.user, e.iq['error']['text'])
#            self.disconnect()
        except IqTimeout:
            print "No response from server."
            self.disconnect()
            
    def ssl_invalid_cert(self, raw_cert):
        pass # Ignore SSL certificate error.
