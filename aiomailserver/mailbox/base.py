from typing import List
from aiomailserver.core.service import MailService
from aiomailserver.auth.base import MailUser


class BaseMailbox(MailService):
    async def store_message(self, user: MailUser, message):
        raise NotImplementedError()

    async def folders(self, user: MailUser) -> List[str]:
        return []

    async def folder_content(self, user: MailUser, folder_name: str):
        raise NotImplementedError()

    async def get_message(self, user: MailUser, folder_name: str,
                          message_id: str):
        raise NotImplementedError()
