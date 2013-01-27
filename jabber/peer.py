from main.models import SMSBot, Processor, Task
from main.device import send_message 
from threading import Thread
import time
import sleekxmpp
from sleekxmpp.exceptions import IqError, IqTimeout
from clientxmpp import AutoRegisterClientXMPP

class SMSEndPointBot(AutoRegisterClientXMPP):

    def __init__(self, jid, password, telnum, peer):
        super(SMSEndPointBot, self).__init__(jid, password)
        self.telnum = telnum
        self.peer = peer
        self.add_event_handler('session_start', self.start)
        self.add_event_handler('session_end', self.end)
        self.add_event_handler('message', self.message)
        self.is_connected = False
        self.register_plugin('xep_0172')
    def start(self, event):
        self.send_presence(pnick = self.telnum)
        self.get_roster()
        # Subscribe to peer
        self.send_presence_subscription(pto=self.peer, pnick = self.telnum, ptype='subscribe')
        
        self.is_connected = True
        print "Bot: %s for %s goes online." % (self.telnum, self.peer)

    def end(self, event):
        self.is_connected = False
        
    def message(self, msg):
        if msg['type'] in ('normal', 'chat'):
            ## Pass on the received message as SMS
            send_message(self.telnum, msg['body'])
            
    def send_msg(self, msg):
        self.send_message(mto=self.peer, mbody=msg)
        return True
        
      
class SMSEndPointThread(Thread):
    def __init__(self, jid, password, telnum, peer, server):
        super(SMSEndPointThread, self).__init__()
        self.daemon = True
        self.server = server
        self.bot = SMSEndPointBot(jid, password, telnum, peer)
        
    def run(self):
        if self.bot.connect(self.server):
            self.bot.process(block=True)
        else:
            print "SMS bot connection failed."

class SMSBotManager(Thread):
    instance = None
    Processor_EndPoint = "xmpp"
    @staticmethod
    def init(server):
        SMSBotManager.instance = SMSBotManager(server)
        SMSBotManager.instance.start()
                    
    def __init__(self, server):
        super(SMSBotManager, self).__init__()
        self.daemon = True
        self.domain = server[0]
        
        qs = Processor.objects.filter(endpoint = SMSBotManager.Processor_EndPoint)
        if not qs.exists():
            self.processor = Processor()
            self.processor.endpoint = SMSBotManager.Processor_EndPoint
            self.processor.receiver = False # As a processor, we send incoming text to recipient
            self.processor.save()
        else:
            self.processor = qs[0]
            
        self.server = server
        self.bots = {} # Activated bot sessions
        for bot in SMSBot.objects.all():
            self.start_bot(bot.jid, bot.password, bot.number, bot.peer)
        
    def start_bot(self, jid, password, telnum, peer):
        """
            Create a new bot thread, adding it to the bots session list.
        """
        assert not jid in self.bots
        t = SMSEndPointThread(jid, password, telnum, peer, self.server)
        self.bots[jid] = t.bot
        t.start()
        return t.bot
        
    def new_bot(self, jid, password, telnum, peer):
        """
            Register a new bot and start it.
        """
        bot_record = SMSBot()
        bot_record.jid = jid
        bot_record.password = password
        bot_record.number = telnum
        bot_record.peer = peer
        bot_record.save()
        
        # Register the user to ejabberd
        #ejabberdctl register dispatcher pi.xurubin.com  a1da234
        
        self.start_bot(jid, password, telnum, peer)
        
    def activate_bot(self, telnum, peer, greeting_msg):
        """
            activate the bot who manages comm between telnum and peer, 
            create a new bot if it does not exists yet.
        """
        if not PeerACL.AllowPeer(telnum, peer):
            print "Access denied for %s to %s" % (peer, telnum)
            return False
        bots = SMSBot.objects.filter(number=telnum)
        jid = None
        if not bots.exists():
            ## Create a new bot
            jid = self.genJid(telnum, peer)
            password = self.genPwd(jid)
            self.new_bot(jid, password, telnum, peer)
        elif bots.count() == 1: # Only one bot can handle a given number,
            # and we need to make sure that the peer matches
            if bots[0].peer != peer:
                return False
            jid = bots[0].jid
        else:
            print "More than one bot is handling %s, something has gone wrong." % telnum
            return False
        
        return self.send_msg(jid, greeting_msg)
    
    def genJid(self, telnum, peer):
        return "%s-%s@%s" % (telnum, peer.split("@")[0], self.domain)
    def genPwd(self, jid):
        return "passw0rd"
    
    def send_msg(self, jid, msg):
        return self.bots[jid].send_msg(msg)
        
    def dispatch_sms(self, telnum, text):
        """
            Called when an incoming sms is received and to be dispatched to the peer
        """
        bots = SMSBot.objects.filter(number=telnum)
        if not bots.exists():
            peer = PeerACL.defaultSink()
        else:
            peer = bots[0].peer
        if not self.activate_bot(telnum, peer, text):
            print "Cannot dispatch message from %s to %s: " % (telnum, peer)
            return False
        return True
    
    def run(self):
        while True:
            qs = Task.objects.filter(processor_id = self.processor.id, processed = False)
            for task in qs:
                if self.dispatch_sms(task.message.number, task.message.text):
                    task.processed = True
                    task.save()
            time.sleep(5)
            
class PeerACL():
    @staticmethod
    def AllowPeer(telnum, peer):
        return peer == PeerACL.defaultSink()
    @staticmethod
    def defaultSink():
        return "xurubin@pi.xurubin.com"
    
def init(server):
    SMSBotManager.init(server)