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
    digit_cmd_map = {
        '433': 'nickinuse',
    }

    def __init__(self, nick, logfile=None, verbosity='INFO'):
        self.nick = self.base_nick = nick

        self.logger = get_logger('ircconnection.logger', logfile, verbosity)

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
        if command.isdigit():
            command = self.convert_digit_cmd(command)

        # we could get nothing if the command is digits format as 433
        # if we get the digits command those we don't know how to handle
        # it, using irc_IGNORECMD instead
        method = getattr(self, "irc_%s" % command.upper(), None)

        try:
            if method is not None:
                method(prefix, params)
            else:
                self.irc_unknown(prefix, command, params)
        except:
            self.logger.error('Method %s not defined' % method)
        
    def convert_digit_cmd(self, cmd):
        real_cmd_name = self.digit_cmd_map.get(cmd, 'ignorecmd')
        return real_cmd_name.upper()

    def irc_NICKINUSE(self, prefix, params):
        ''' 
            handle message like this:
            :wright.freenode.net 433 * oupeng-bot :Nickname is already in use.
        '''
        # seems there is already a oupeng-bot running now
        self.disconnect_ircserver()

    def irc_unknown(self, prefix, command, params):
        """
        Called by L{handleCommand} on a command that doesn't have a defined
        handler. Subclasses should override this method.
        """
        raise NotImplementedError(command, prefix, params)

    def irc_IGNORECMD(self, prefix, command, params):
        self.logger.info('command %s ignored' % command)

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
        self.gpool.kill()
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
            self.channel = channel
        
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
