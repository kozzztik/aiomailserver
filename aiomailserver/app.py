import logging

logging.basicConfig(level=logging.DEBUG)

from aiomailserver.core.controller import MailServerController
import asyncio

def exception_handler(*args, **kwargs):
    logging.exception(args)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.set_exception_handler(exception_handler)
    server = MailServerController(loop=loop)
    server.loop.run_until_complete(server.start())
    try:
        server.loop.run_forever()
    finally:
        server.loop.run_until_complete(server.close())
