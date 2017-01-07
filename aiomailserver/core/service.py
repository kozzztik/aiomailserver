class MailService:
    def __init__(self, controller, settings, loop):
        self.controller = controller
        self.loop = loop
        self.settings = settings

    async def start(self):
        pass

    async def close(self):
        pass
