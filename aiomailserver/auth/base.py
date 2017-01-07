from typing import Optional
from aiomailserver.core.service import MailService


class MailUser:
    def __init__(self, name, domain):
        self.name = name
        self.domain = domain


class BaseAuthBackend(MailService):
    async def check_domain(self, domain_name) -> bool:
        return True

    async def check_user(self, name: str, domain: str) -> bool:
        return True

    async def auth_user(self, name, domain, password) -> Optional[MailUser]:
        return MailUser(name, domain)
