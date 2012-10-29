# -*- coding: utf8 -*-

import sys
import logging
import random
import re

from logging.handlers import RotatingFileHandler

import gevent
from gevent import socket


class IRCBot(object):
    nick_re = re.compile('.*?Nickname is already in use')
    nick_change_re = re.compile(':(?P<old_nick>.*?)!\S+\s+?NICK\s+:\s*(?P<new_nick>[-\w]+)')
    ping_re = re.compile('^PING (?P<payload>.*)')
    chanmsg_re = re.compile(':(?P<nick>.*?)!\S+\s+?PRIVMSG\s+(?P<channel>#+[-\w]+)\s+:(?P<message>[^\n\r]+)')
    privmsg_re = re.compile(':(?P<nick>.*?)!~\S+\s+?PRIVMSG\s+[^#][^:]+:(?P<message>[^\n\r]+)')
    part_re = re.compile(':(?P<nick>.*?)!\S+\s+?PART\s+(?P<channel>#+[-\w]+)')
    join_re = re.compile(':(?P<nick>.*?)!\S+\s+?JOIN\s+:\s*(?P<channel>#+[-\w]+)')
    quit_re = re.compile(':(?P<nick>.*?)!\S+\s+?QUIT\s+.*')

    # mapping for logging verbosity
    verbosity_map = {
        0: logging.ERROR,
        1: logging.INFO,
        2: logging.DEBUG,
    }

    def __init__(self, nick, logfile=None, verbosity=1):
        self.nick = self.base_nick = nick

        self._callbacks = []

        self.logfile = logfile
        self.verbosity = verbosity
        self.logger = self.get_logger('ircconnection.logger', self.logfile)

        # for help info
        self.capabilities = []

    def get_logger(self, logger_name, filename):
        log = logging.getLogger(logger_name)
        log.setLevel(self.verbosity_map.get(self.verbosity, logging.INFO))
        
        if self.logfile:
            handler = RotatingFileHandler(filename, maxBytes=1024*1024, backupCount=2)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            log.addHandler(handler)
        
        if self.verbosity == 2 or not self.logfile:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            log.addHandler(stream_handler)
        
        return log

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
            self.handle(message)

    def handle(self, msg):
        patterns = self.dispatch_patterns()
        self.logger.info('Handle %s' % msg)

        for pattern, callback in patterns:
            match = pattern.match(msg)
            if match:
                callback(**match.groupdict())

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

    def handle_ping(self, payload):
        """
        Respond to periodic PING messages from server
        """
        self.logger.info('server ping: %s' % payload)
        self.send('PONG %s' % payload)

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
