# -*- coding: utf8 -*-

import sys
import random
import re

import gevent
from gevent import socket
from gevent.pool import Pool

from tools import get_logger


class IRCBadMessage(BaseException):
    pass


class IRCBot(object):
    nick_re = re.compile('.*?Nickname is already in use')
    nick_change_re = re.compile(':(?P<old_nick>.*?)!\S+\s+?NICK\s+:\s*(?P<new_nick>[-\w]+)')
    ping_re = re.compile('^PING (?P<payload>.*)')
    chanmsg_re = re.compile(':(?P<nick>.*?)!\S+\s+?PRIVMSG\s+(?P<channel>#+[-\w]+)\s+:(?P<message>[^\n\r]+)')
    privmsg_re = re.compile(':(?P<nick>.*?)!~\S+\s+?PRIVMSG\s+[^#][^:]+:(?P<message>[^\n\r]+)')
    part_re = re.compile(':(?P<nick>.*?)!\S+\s+?PART\s+(?P<channel>#+[-\w]+)')
    join_re = re.compile(':(?P<nick>.*?)!\S+\s+?JOIN\s+:\s*(?P<channel>#+[-\w]+)')
    quit_re = re.compile(':(?P<nick>.*?)!\S+\s+?QUIT\s+.*')

    def __init__(self, nick, logfile=None, verbosity='INFO'):
        self.nick = self.base_nick = nick

        self._callbacks = []

        self.logger = get_logger('ircconnection.logger', logfile, verbosity)

        # for help info
        self.capabilities = []

        # gevent pool
        self.gpool = Pool(10)

    def parsemsg(self, msg):
        """
            Breaks a message from an IRC server into its prefix, command, and arguments.
        """
        prefix = ''
        trailing = []

        '''
            according to rfc2812, the message format is:
            :<prefix> <command> <params> :<trailing>

            here are some examples:
            :CalebDelnay!calebd@localhost PRIVMSG #mychannel :Hello everyone!
            :CalebDelnay!calebd@localhost QUIT :Bye bye!
            :CalebDelnay!calebd@localhost JOIN #mychannel
            :CalebDelnay!calebd@localhost MODE #mychannel -l
            PING :irc.localhost.localdomain
        '''
        if not msg:
            raise IRCBadMessage("Empty line.")

        if msg[0] == ':':
            prefix, msg = msg[1:].split(' ', 1)

        if msg.find(' :') != -1:
            msg, trailing = msg.split(' :', 1)
            args = msg.split()
            args.append(trailing)

        else:
            args = msg.split()

        command = args.pop(0)

        return prefix, command, args

    def _handleMsg(self, prefix, command, params):
        """
            Determine the function to call for the given command and call it with
            the given arguments.
        """
        method = getattr(self, "irc_%s" % command.upper(), None)
        try:
            if method is not None:
                method(prefix, params)
            else:
                self.irc_unknown(prefix, command, params)
        except:
            self.logger.error('Method %s not defined' % method)

    def irc_unknown(self, prefix, command, params):
        """
        Called by L{handleCommand} on a command that doesn't have a defined
        handler. Subclasses should override this method.
        """
        raise NotImplementedError(command, prefix, params)

    def connect_ircserver(self, server, port):
        self.server = server
        self.port = port

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._socket.connect((self.server, self.port))
        except socket.error:
            self.logger.error('Unable to connect to %s on port %d' % (self.server, self.port), exc_info=1)
            sys.exit(1)

        self._sock_file = self._socket.makefile()

        self.register_nick()
        self.register()

    def disconnect_ircserver(self):
        self._socket.close()

    def send(self, msg):
        if not msg.endswith('\r\n'):
            msg += '\r\n'
        
        self.logger.info(msg)     
        self._sock_file.write(msg)
        self._sock_file.flush()

    def join_channel(self, channel):
        if not channel.startswith('#'):
            channel = '#%s' % channel
        
        self.logger.debug('joining %s' % channel)
        self.send('JOIN %s' % channel)

        self._enter_eventloop()

    def _enter_eventloop(self):
        self.running = True
        while self.running:
            try:
                message = self._sock_file.readline()
            except socket.error:
                message = None
            
            if not message:
                self.disconnect_ircserver()
                return True
            
            message = message.rstrip()
            self.gpool.spawn(self.handle, message)

    def handle(self, msg):
        self.logger.info('Handle %s' % msg)
        prefix, command, params = self.parsemsg(msg)
        self._handleMsg(prefix, command, params)

    def register_nick(self):
        self.logger.info('Registering nick %s' % self.nick)
        self.send('NICK %s' % self.nick)

    def register(self):
        self.logger.info('Authing as %s' % self.nick)
        self.send('USER %s %s bla :%s' % (self.nick, self.server, self.nick))

    def part(self, channel):
        if not channel.startswith('#'):
            channel = '#%s' % channel
        self.send('PART %s' % channel)
        self.logger.debug('leaving %s' % channel)

    def respond(self, message, channel=None, nick=None):
        """
        Multipurpose method for sending responses to channel or via message to
        a single user
        """
        if channel:
            if not channel.startswith('#'):
                channel = '#%s' % channel
            self.send('PRIVMSG %s :%s' % (channel, message))
        elif nick:
            self.send('PRIVMSG %s :%s' % (nick, message))
    
    def dispatch_patterns(self):
        """
        Low-level dispatching of socket data based on regex matching, in general
        handles
        
        * In event a nickname is taken, registers under a different one
        * Responds to periodic PING messages from server
        * Dispatches to registered callbacks when
            - any user leaves or enters a room currently connected to
            - a channel message is observed
            - a private message is received
        """
        return (
            (self.nick_re, self.new_nick),
            (self.nick_change_re, self.handle_nick_change),
            (self.ping_re, self.handle_ping),
            (self.part_re, self.handle_part),
            (self.join_re, self.handle_join),
            (self.quit_re, self.handle_quit),
            (self.chanmsg_re, self.handle_channel_message),
            (self.privmsg_re, self.handle_private_message),
        )
    
    def register_callbacks(self, callbacks):
        """
        Hook for registering custom callbacks for dispatch patterns
        """
        self._callbacks.extend(callbacks)
    
    def new_nick(self):
        """
        Generates a new nickname based on original nickname followed by a
        random number
        """
        old = self.nick
        self.nick = '%s_%s' % (self.base_nick, random.randint(1, 1000))
        self.logger.warn('Nick %s already taken, trying %s' % (old, self.nick))
        self.register_nick()
        self.handle_nick_change(old, self.nick)

    def handle_nick_change(self, old_nick, new_nick):
        for pattern, callback in self._callbacks:
            if pattern.match('/nick'):
                callback(old_nick, '/nick', new_nick)

    def irc_PING(self, prefix, params):
        """
            NOTE: ONLY response to periodic PING messages from server 

            If there is no prefix, then the source of the 
            message is the server for the current connection, 
            as in this PING method
        """
        assert prefix == '', 'where is this PING message from?'
        log_text = 'ping: prefix=>[%s], params=>[%s]'
        self.logger.info(log_text % (prefix, ' '.join(params)))

        # ping message from server
        self.send('PONG :%s' % params[0])

    def handle_part(self, nick, channel):
        for pattern, callback in self._callbacks:
            if pattern.match('/part'):
                callback(nick, '/part', channel)
    
    def handle_join(self, nick, channel):
        for pattern, callback in self._callbacks:
            if pattern.match('/join'):
                callback(nick, '/join', channel)
    
    def handle_quit(self, nick):
        for pattern, callback in self._callbacks:
            if pattern.match('/quit'):
                callback(nick, '/quit', None)
    
    def _process_command(self, nick, message, channel):
        results = []
        
        for pattern, callback in self._callbacks:
            match = pattern.match(message) or pattern.match('/privmsg')
            if match:
                res = callback(nick, message, channel, **match.groupdict())
                if isinstance(res, list):
                    results.extend(res)
                else:
                    results.append(res)
        
        return results
    
    def handle_channel_message(self, nick, channel, message):
        for result in self._process_command(nick, message, channel):
            if result:
                self.respond(result, nick=nick)
    
    def handle_private_message(self, nick, message):
        for result in self._process_command(nick, message, None):
            if result:
                self.respond(result, nick=nick)
