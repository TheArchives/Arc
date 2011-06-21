# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import web
try:
    import simplejson
except:
    import json as simplejson
import socket
import configuration as config

urls=(
    '/', 'status',
    '/index', 'status',
    '/(.*).css', 'css'
)
render = web.template.render('templates/')
app = web.application(urls, globals())
BACKEND_HOST = config.host
BACKEND_PORT = config.port
BACKEND_PASSWORD = config.password

class BackendSocket(object):
    
    def __init__(self, host, port, password):
        self.skt = socket.socket()
        self.skt.connect((host, port))
        self.password = password
    
    def query(self, command, data=None):
        payload = {
            "command": command,
            "password": self.password,
        }
        if data:
            payload.update(data)
        self.skt.send(simplejson.dumps(payload)+"\r\n")
        response = self.skt.recv(1024)
        while response and "\n" not in response:
            response += self.skt.recv(1024)
            if response == "":
                break
        if "\n" in response:
            result, response = response.split("\n", 1)
            return simplejson.loads(result)
        else:
            raise IOError
    
    def __del__(self):
        self.skt.close()
    

class status:
    def GET(self):
        bs = BackendSocket(BACKEND_HOST, BACKEND_PORT, BACKEND_PASSWORD)
        name = bs.query("name")['name']
        motd = bs.query("motd")['motd']
        public = bs.query("public")['public']
        limit = bs.query("limit")['limit']
        awaytime = bs.query("awaytime")['awaytime']
        asd = bs.query("asd")['asd']
        gchat = bs.query("gchat")['gchat']
        bufreq = bs.query("bufreq")['bufreq']
        bumax = bs.query("bumax")['bumax']
        ircserver = bs.query("ircserver")['ircserver']
        ircchannel = bs.query("ircchannel")['ircchannel']
        owner = bs.query("owner")['owner']
        specs = bs.query("specs")['specs']
        worlds = sorted(bs.query("userworlds")['worlds'])
        users = bs.query("users")['users']
        directors = bs.query("directors")['directors']
        admins = bs.query("Admins")['admins']
        mods = bs.query("Mods")['mods']
        members = bs.query("Members")['members']
        return render.status(name, motd, public, limit, awaytime, asd, gchat, bufreq, bumax, ircserver, ircchannel, owner, specs, worlds, users, directors, admins, mods, members)

class css:
     def GET(self, css):
        styling = open(css+".css", 'rb')
        return styling.read()
        styling.close()

if __name__ == "__main__": app.run()
