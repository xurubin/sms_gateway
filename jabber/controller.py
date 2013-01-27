import sleekxmpp
from clientxmpp import AutoRegisterClientXMPP
from peer import SMSBotManager

class ControllerBot(AutoRegisterClientXMPP):

    def __init__(self, jid, password):
        super(ControllerBot, self).__init__(jid, password)
        
        self.add_event_handler('session_start', self.start)
        self.add_event_handler('message', self.message)
        
    def start(self, event):
        self.send_presence()
        self.get_roster()
        print "Dispatcher goes online"
        
    def message(self, msg):
        if msg['type'] in ('normal', 'chat'):
            msg.reply(self.handle_command(msg)).send()
            
    def handle_command(self, msg):
        message = msg['body']
        command = message.split(" ")
        if command[0].lower() == "to" and len(command) == 2:
            number = command[1]
            peer = msg['from'].bare
            if SMSBotManager.instance.activate_bot(number, peer, "Hello I'm your handler for %s" % number):
                return "Succeeded"
            else:
                return "Failed"
        return "Echo: " + message
        
def run(server):
    controller = ControllerBot("dispatcher@%s" % server[0], "a1da234")
    #controller.register_plugin('xep_0030') # Service Discovery
    #controller.register_plugin('xep_0199') # Ping
    if controller.connect(server):
        controller.process(block=True)
    else:
        print "controller bot connection failed."