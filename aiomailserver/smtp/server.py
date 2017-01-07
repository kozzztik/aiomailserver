from asyncio import BaseEventLoop

from aiomailserver.core.service import MailService

from .handler import SMTPHandler
from .protocol import ExtendedSMTP


class SMTPServer(MailService):
    def __init__(self, controller, settings, loop: BaseEventLoop):
        super(SMTPServer, self).__init__(controller, settings, loop)
        self.host = settings['host']
        self.port = settings['port']
        self.server = None
        self.handler = SMTPHandler(self)

    def factory(self):
        return ExtendedSMTP(self.handler, loop=self.loop)

    async def start(self):
        self.server = await self.loop.create_server(
            self.factory,
            host=self.host,
            port=self.port
        )

    async def close(self):
        if self.server:
            self.server.close()
            self.server = None
