import pytest
from types import SimpleNamespace
from telegram import Message, User, Chat
from telegram.ext import ContextTypes

from bot_telegram_polling import TelegramBot


class DummyMessage:
    def __init__(self, text=None, caption=None, entities=None, reply_to_message=None):
        self.text = text
        self.caption = caption
        self.entities = entities
        self.caption_entities = None
        self.reply_to_message = reply_to_message


class DummyEntity:
    def __init__(self, type, offset, length):
        self.type = type
        self.offset = offset
        self.length = length


class DummyUpdate:
    def __init__(self, message=None, chat_type='private'):
        self.message = message
        self.effective_chat = SimpleNamespace(id=1, type=chat_type)
        self.effective_user = SimpleNamespace(id=123, username='tester', first_name='Test')


class DummyContext:
    def __init__(self):
        self.bot = SimpleNamespace()


@pytest.mark.asyncio
async def test_extract_client_number():
    tb = TelegramBot()
    assert tb._extract_client_number('cliente 12345') == '12345'
    assert tb._extract_client_number('no digits') == ''
    assert tb._extract_client_number('id: 12') == ''  # default min length 3


@pytest.mark.asyncio
async def test_mention_detection():
    tb = TelegramBot()
    # set fake bot_info
    tb.bot_info = SimpleNamespace(username='mybot', id=999)

    msg = DummyMessage(text='hola @mybot 123')
    update = DummyUpdate(message=msg, chat_type='group')

    assert tb._is_mentioned_in_message(msg) is True


@pytest.mark.asyncio
async def test_addressed_and_processed_text_private():
    tb = TelegramBot()
    msg = DummyMessage(text='12345')
    update = DummyUpdate(message=msg, chat_type='private')
    ctx = DummyContext()

    addressed, processed = await tb._addressed_and_processed_text(update, ctx)
    assert addressed is True
    assert processed == '12345'


@pytest.mark.asyncio
async def test_addressed_and_processed_text_mention():
    tb = TelegramBot()
    tb.bot_info = SimpleNamespace(username='mybot', id=999)
    msg = DummyMessage(text='@mybot 12345')
    update = DummyUpdate(message=msg, chat_type='group')
    ctx = DummyContext()

    addressed, processed = await tb._addressed_and_processed_text(update, ctx)
    assert addressed is True
    assert '12345' in processed
