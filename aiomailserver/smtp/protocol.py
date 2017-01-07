import asyncio
try:
    import ssl
    from asyncio import sslproto
except ImportError:                                 # pragma: nocover
    _has_ssl = False
else:                                               # pragma: nocover
    _has_ssl = True

from aiosmtpd.smtp import SMTP, log


class SessionContext:
    peer = None
    ssl = None
    host_name = None


class MessageContext:
    mailfrom = None
    mail_options = None
    received_data = None

    def __init__(self):
        self.rcpttos = []
        self.rcpt_options = []


class ExtendedSMTP(SMTP):
    def __init__(self, *args, **kwargs):
        super(ExtendedSMTP, self).__init__(*args, **kwargs)
        self.session = self._create_session_context()
        self.transport = None

    def _create_session_context(self):
        return SessionContext()

    def _create_message_context(self):
        return MessageContext()

    def connection_made(self, transport):
        super(ExtendedSMTP, self).connection_made(transport)
        self.session.peer = transport.get_extra_info('peername')

    def _set_post_data_state(self):
        """Reset state variables to their post-DATA state."""
        super(ExtendedSMTP, self)._set_post_data_state()
        self.message = self._create_message_context()
        self.require_SMTPUTF8 = False

    # SMTP and ESMTP commands
    @asyncio.coroutine
    def smtp_HELO(self, hostname):
        if not hostname:
            yield from self.push('501 Syntax: HELO hostname')
            return
        # See issue #21783 for a discussion of this behavior.
        if self.seen_greeting:
            yield from self.push('503 Duplicate HELO/EHLO')
            return
        self._set_rset_state()
        self.seen_greeting = hostname
        self.session.host_name = hostname
        yield from self.push('250 %s' % self.hostname)

    @asyncio.coroutine
    def smtp_EHLO(self, arg):
        if not arg:
            yield from self.push('501 Syntax: EHLO hostname')
            return
        # See issue #21783 for a discussion of this behavior.
        if self.seen_greeting:
            yield from self.push('503 Duplicate HELO/EHLO')
            return
        self._set_rset_state()
        self.session.host_name = arg
        self.seen_greeting = arg
        self.extended_smtp = True
        yield from self.push('250-%s' % self.hostname)
        if self.data_size_limit:
            yield from self.push('250-SIZE %s' % self.data_size_limit)
            self.command_size_limits['MAIL'] += 26
        if not self._decode_data:
            yield from self.push('250-8BITMIME')
        if self.enable_SMTPUTF8:
            yield from self.push('250-SMTPUTF8')
            self.command_size_limits['MAIL'] += 10
        yield from self.ehlo_hook()
        yield from self.push('250 HELP')

    @asyncio.coroutine
    def smtp_MAIL(self, arg):
        if not self.seen_greeting:
            yield from self.push('503 Error: send HELO first')
            return
        log.debug('===> MAIL %s', arg)
        syntaxerr = '501 Syntax: MAIL FROM: <address>'
        if self.extended_smtp:
            syntaxerr += ' [SP <mail-parameters>]'
        if arg is None:
            yield from self.push(syntaxerr)
            return
        arg = self._strip_command_keyword('FROM:', arg)
        address, params = self._getaddr(arg)
        if not address:
            yield from self.push(syntaxerr)
            return
        if not self.extended_smtp and params:
            yield from self.push(syntaxerr)
            return
        if self.mailfrom:
            yield from self.push('503 Error: nested MAIL command')
            return
        mail_options = params.upper().split()
        params = self._getparams(mail_options)
        if params is None:
            yield from self.push(syntaxerr)
            return
        if not self._decode_data:
            body = params.pop('BODY', '7BIT')
            if body not in ['7BIT', '8BITMIME']:
                yield from self.push(
                    '501 Error: BODY can only be one of 7BIT, 8BITMIME')
                return
        if self.enable_SMTPUTF8:
            smtputf8 = params.pop('SMTPUTF8', False)
            if smtputf8 is True:
                self.require_SMTPUTF8 = True
            elif smtputf8 is not False:
                yield from self.push('501 Error: SMTPUTF8 takes no arguments')
                return
        size = params.pop('SIZE', None)
        if size:
            if isinstance(size, bool) or not size.isdigit():
                yield from self.push(syntaxerr)
                return
            elif self.data_size_limit and int(size) > self.data_size_limit:
                yield from self.push(
                    '552 Error: message size exceeds fixed maximum message '
                    'size')
                return
        if len(params.keys()) > 0:
            yield from self.push(
                '555 MAIL FROM parameters not recognized or not implemented')
            return
        self.message.mailfrom = address
        self.message.mail_options = mail_options
        log.info('sender: %s', address)
        yield from self.push('250 OK')

    @asyncio.coroutine
    def smtp_RCPT(self, arg):
        if not self.seen_greeting:
            yield from self.push('503 Error: send HELO first')
            return
        log.debug('===> RCPT %s', arg)
        if not self.mailfrom:
            yield from self.push('503 Error: need MAIL command')
            return
        syntaxerr = '501 Syntax: RCPT TO: <address>'
        if self.extended_smtp:
            syntaxerr += ' [SP <mail-parameters>]'
        if arg is None:
            yield from self.push(syntaxerr)
            return
        arg = self._strip_command_keyword('TO:', arg)
        address, params = self._getaddr(arg)
        if not address:
            yield from self.push(syntaxerr)
            return
        if not self.extended_smtp and params:
            yield from self.push(syntaxerr)
            return
        rcpt_options = params.upper().split()
        params = self._getparams(rcpt_options)
        if params is None:
            yield from self.push(syntaxerr)
            return
        # XXX currently there are no options we recognize.
        if len(params) > 0:
            yield from self.push(
                '555 RCPT TO parameters not recognized or not implemented')
            return
        self.message.rcpttos.append(address)
        self.message.rcpt_options.append(rcpt_options)
        log.info('recips: %s', address)
        yield from self.push('250 OK')

    @asyncio.coroutine
    def smtp_DATA(self, arg):
        if not self.seen_greeting:
            yield from self.push('503 Error: send HELO first')
            return
        if not self.rcpttos:
            yield from self.push('503 Error: need RCPT command')
            return
        if arg:
            yield from self.push('501 Syntax: DATA')
            return
        yield from self.push('354 End data with <CR><LF>.<CR><LF>')
        data = []
        self.num_bytes = 0
        while not self.connection_closed:
            line = yield from self._reader.readline()
            if line == b'.\r\n':
                break
            self.num_bytes += len(line)
            if self.data_size_limit and self.num_bytes > self.data_size_limit:
                yield from self.push('552 Error: Too much mail data')
            # XXX this rstrip may not exactly preserve the old behavior
            line = line.rstrip(b'\r\n')
            if self._decode_data:
                data.append(line.decode('utf-8'))
            else:
                data.append(line)
        # Remove extraneous carriage returns and de-transparency
        # according to RFC 5321, Section 4.5.2.
        for i in range(len(data)):
            text = data[i]
            if text and text[0] == self._dotsep:
                data[i] = text[1:]
        self.message.received_data = self._newline.join(data)
        args = (self.session, self.message)
        kwargs = {'loop': self.loop}
        if asyncio.iscoroutinefunction(self.event_handler.process_message):
            status = yield from self.event_handler.process_message(
                *args, **kwargs)
        else:
            status = self.event_handler.process_message(*args, **kwargs)
        self._set_post_data_state()
        if status:
            yield from self.push(status)
        else:
            yield from self.push('250 OK')
