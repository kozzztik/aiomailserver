import asyncio
from .settings import Settings
from .service import MailService


class MailServerController:
    def __init__(self, settings=None, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.settings = Settings(settings)
        self.services = []
        for config in self.settings['SERVICES']:
            self.services.append(self._get_service_instance(config))

    @staticmethod
    def _get_class(name) -> type:
        if isinstance(name, type):
            return name
        assert isinstance(name, str)
        name = name.split('.')
        used = name.pop(0)
        found = __import__(used)
        for n in name:
            used = used + '.' + n
            try:
                found = getattr(found, n)
            except AttributeError:
                __import__(used)
                found = getattr(found, n)
        return found

    def _get_service_instance(self, config: dict):
        config = config.copy()
        class_name = config.pop('class')
        cls = self._get_class(class_name)
        assert issubclass(cls, MailService)
        return cls(self, config, self.loop)

    async def start(self):
        for service in self.services:
            await service.start()

    async def close(self):
        for service in self.services:
            await service.close()

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
