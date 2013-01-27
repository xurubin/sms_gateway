import datetime
import logging
import re
import serial


pat = re.compile(r'\+CMGL: (?P<index>\d+),'
                 '"(?P<status>.+?)",'
                 '"(?P<number>.*?)",'
                 '("(?P<name>.*?)")?,'
                 '("(?P<date>.+?)")?\r\n'
                 )

logger = logging.getLogger('sms.modem')

class ModemError(RuntimeError):
    pass

class FixedOffset(datetime.tzinfo):
    """Fixed offset in minutes east from UTC."""
    ZERO = datetime.timedelta(0)
    def __init__(self):
        self.__offset = FixedOffset.ZERO
        self.__name = "FixedOffset"
    
    def setOffset(self, offset):
        self.__offset = datetime.timedelta(minutes = offset)
        return self
    
    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return FixedOffset.ZERO
    
class Message(object):
    """A received SMS message"""

    format = '%y/%m/%d,%H:%M:%S'

    def __init__(self, index, modem, number, date, text):
        self.index = index
        self.modem = modem
        self.number = number
        if date is not None:
            # modem incorrectly reports UTC time rather than local
            # time so ignore time zone info
            ndate = datetime.datetime.strptime(date[:-3], self.format)
            self.date = datetime.datetime(ndate.year, ndate.month, ndate.day, ndate.hour, ndate.minute, ndate.second, ndate.microsecond, FixedOffset().setOffset(60 * int(date[-3:])))
        self.text = text

    def delete(self):
        response = self.modem._command('AT+CMGD=%d' % self.index)
        ok = False
        for line in response:
            if 'OK' in line:
                ok = True
        if not ok:
            raise ModemError('Delete of message %d seemed to fail' 
                             % self.index)


class Modem(object):
    """Provides access to a gsm modem"""
    
    def __init__(self, dev_id, baud):
        self.conn = serial.Serial(dev_id, baud, timeout=1, rtscts=0)
        # make sure modem is OK
        self._command('AT')

    def send(self, number, message):
        """Send a SMS message

        number should start with 1
        message should be no more than 160 ASCII characters.
        """
        self._command('AT+CMGS="%s"' % number)
        self._command(message + '\x1A', flush=False)

    def messages(self):
        """Return received messages"""
        msgs = []
        text = None
        index = None
        date = None
        for line in self._command('AT+CMGL="ALL"')[:-1]:
            m = pat.match(line)
            if m is not None:
                if text is not None:
                    msgs.append(Message(index, self, number, date, text))
                status = m.group('status')
                index = int(m.group('index'))
                number = m.group('number')
                date = m.group('date')
                text = ''
            elif text is not None:
                if line == '\r\n':
                    text += '\n'
                else:
                    text += line.strip()
        if text is not None:
            msgs.append(Message(index, self, number, date, text))
        return msgs
    
    def wait(self, timeout=None):
        """Blocking wait until a message is received or timeout (in secs)"""
        old_timeout = self.conn.timeout
        self.conn.timeout = timeout
        results = self.conn.read()
        logger.debug('wait read "%s"' % results)
        self.conn.timeout = old_timeout
        results = self.conn.readlines()
        logger.debug('after wait read "%s"' % results)
        
    def _command(self, at_command, flush=True):
        logger.debug('sending "%s"' % at_command)
        self.conn.write(at_command)
        if flush:
            self.conn.write('\r\n')
            #logger.debug('sending crnl')
        results = self.conn.readlines()
        logger.debug('received "%s"' % results)
        for line in results:
            if 'ERROR' in line:
                raise ModemError(results)
        return results
    
    def __del__(self):
        try:
            self.conn.close()
        except AttributeError:
            pass
