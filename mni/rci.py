import urllib2

SERIAL = 'serial'
OUT = 'out'
IN = 'in'

DCD = 1
CTS = 2
DSR = 3
RTS = 4
DTR = 5

class RCI:

    def __init__(self, ip, user='root', password='dbps'):
        self.ip = ip
        self.user = user
        self.password = password
        auth_handler = urllib2.HTTPBasicAuthHandler()
        auth_handler.add_password(realm='Digi Connect ME',
                uri='http://%s/UE/rci'%(self.ip),
                user=self.user,
                passwd=self.password)
        self.opener = urllib2.build_opener(auth_handler)

    def get_settings(self):
        rcirequest = """
<rci_request version="1.1">
    <query_setting>
        <boot/>
        <serial/>
    </query_setting>
</rci_request>
"""
        f = self.opener.open('http://%s/UE/rci'%(self.ip), data=rcirequest)
        return f.readlines()

    def set_gpio_mode(self, gpio, mode):
        rcirequest = """
<rci_request version="1.1">
    <set_setting>
        <gpio_mode>
            <pin%d>%s</pin%d>
        </gpio_mode>
    </set_setting>
</rci_request>
"""%(gpio, mode, gpio)

        f = self.opener.open('http://%s/UE/rci'%(self.ip), data=rcirequest)
        return f.readlines()

    def set_gpio_high(self, gpio):
        rcirequest = """
<rci_request version="1.1">
     <set_setting>
         <gpio_mode>
             <pin%d>out</pin%d>
         </gpio_mode>
     </set_setting>
     <set_state>
        <gpio>
            <pin%d>asserted</pin%d>
        </gpio>
    </set_state>
</rci_request>
"""%(gpio, gpio, gpio, gpio)

        f = self.opener.open('http://%s/UE/rci'%(self.ip), data=rcirequest)
        return f.readlines()

    def set_gpio_low(self, gpio):
        rcirequest = """
<rci_request version="1.1">
     <set_setting>
         <gpio_mode>
             <pin%d>out</pin%d>
         </gpio_mode>
     </set_setting>
     <set_state>
        <gpio>
            <pin%d>unasserted</pin%d>
        </gpio>
    </set_state>
</rci_request>
"""%(gpio, gpio, gpio, gpio)

        f = self.opener.open('http://%s/UE/rci'%(self.ip), data=rcirequest)
        return f.readlines()



if __name__=="__main__":
    rci = RCI('172.17.6.102')

    print rci.get_settings()

    #print rci.set_gpio_high(RTS)
    rci = RCI('172.17.6.103')

    print rci.get_settings()


