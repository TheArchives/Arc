# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import urllib, urllib2
import simplejson as json

class McBans():
    def __init__(self, apikey):
        self.url = "http://72.10.39.172/v2/"
        self.key = apikey
    
    def _request(self, data):
        """Convenience function to send data to MCBans"""
        data = urllib.urlencode(data)
        request = urllib2.Request(self.url+self.key, data)
        response = urllib2.urlopen(request)
        readable = json.loads(response.read())
        return readable
        
    # Connection activity
        
    def connect(self, player, ip):
        data = {"player": player, "ip": ip, "exec": "playerConnect"}
        values = self._request(data)
        return values # {'banStatus': 'n', 'playerRep': 10, 'altList': 'username: REP 0, username: REP 10'(, 'banReason': 'banned')}
        
    def disconnect(self, player):
        data = {"player": player, "exec": "playerDisconnect"}   
        values = self._request(data)
        return values # {'result': 'y'}
    
    # Banning activity
    
    def unban(self, player, admin):
        data = {"player": player, "admin": admin, "exec": "unBan"}
        values = self._request(data)
        return values # {"result": "y"}
    
    def localBan(self, player, ip, reason, admin):
        data = {"player": player, "ip": ip, "reason": reason, "admin": admin, "exec": "localBan"}
        values = self._request(data)
        return values # {"result": "y"}
        
    def globalBan(self, player, ip, reason, admin):
        data = {"player": player, "ip": ip, "reason": reason, "admin": admin, "exec": "globalBan"}
        values = self._request(data)
        return values # {"result": "y"}
    
    def tempBan(self, player, ip, reason, admin, duration, measure):
        if measure is ("m" or "h" or "d"):
            data = {"player": player, "ip": ip, "reason": reason, "admin": admin, "duration": duration, "measure": measure, "exec": "tempBan"}
            values = self._request(data)
        else:
            raise ValueError("'measure' must be m, h or d!")
        return values # {"result": "y"}
    
    # Lookups
    
    def lookup(self, player, admin="None"):
        data = {"player": player, "admin": admin, "exec": "playerLookup"}
        values = self._request(data)
        return values # {'global': ['servername .:. reason', 'servername .:. reason'], u'total': 4, u'local': ['servername .:. reason'], 'reputation': 5}
        
    # Account confirmation
    
    def confirm(self, player, key):
        data = {"player": player, "string": key, "exec": "playerSet"}
        values = self._request(data)
        return values # {"result": "n"}