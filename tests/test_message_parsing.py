import pytest
import os
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
    def __init__(self, type, offset=0, length=0, user=None):
        self.type = type
        self.offset = offset
        self.length = length
        self.user = user


class DummyUpdate:
    def __init__(self, message=None, chat_type='private'):
        self.message = message
        self.effective_chat = SimpleNamespace(id=1, type=chat_type)
        self.effective_user = SimpleNamespace(id=123, username='tester', first_name='Test')


class DummyContext:
    def __init__(self):
        self.bot = SimpleNamespace()


def build_test_bot():
    tb = TelegramBot.__new__(TelegramBot)
    tb.bot_info = None
    tb.min_client_digits = 3
    tb._normalize_phone = lambda raw: ''.join(ch for ch in str(raw) if ch.isdigit()).lstrip('0')
    tb._get_normalize_fn = lambda: tb._normalize_phone
    return tb


@pytest.mark.asyncio
async def test_extract_client_number():
    tb = build_test_bot()
    assert tb._extract_client_number('cliente 12345') == '12345'
    assert tb._extract_client_number('no digits') == ''
    assert tb._extract_client_number('id: 12') == ''  # default min length 3


@pytest.mark.asyncio
async def test_mention_detection():
    tb = build_test_bot()
    # set fake bot_info
    tb.bot_info = SimpleNamespace(username='mybot', id=999)

    msg = DummyMessage(text='hola @mybot 123')
    update = DummyUpdate(message=msg, chat_type='group')

    assert tb._is_mentioned_in_message(msg) is True


@pytest.mark.asyncio
async def test_addressed_and_processed_text_private():
    tb = build_test_bot()
    msg = DummyMessage(text='12345')
    update = DummyUpdate(message=msg, chat_type='private')
    ctx = DummyContext()

    addressed, processed = await tb._addressed_and_processed_text(update, ctx)
    assert addressed is True
    assert processed == '12345'


@pytest.mark.asyncio
async def test_addressed_and_processed_text_mention():
    tb = build_test_bot()
    tb.bot_info = SimpleNamespace(username='mybot', id=999)
    msg = DummyMessage(text='@mybot 12345')
    update = DummyUpdate(message=msg, chat_type='group')
    ctx = DummyContext()

    addressed, processed = await tb._addressed_and_processed_text(update, ctx)
    assert addressed is True
    assert '12345' in processed


@pytest.mark.asyncio
async def test_addressed_and_processed_text_group_direct_number_enabled(monkeypatch):
    monkeypatch.setenv('ALLOW_DIRECT_GROUP_NUMBER', 'true')
    tb = build_test_bot()
    tb.bot_info = SimpleNamespace(username='mybot', id=999)
    msg = DummyMessage(text='5536604547')
    update = DummyUpdate(message=msg, chat_type='group')
    ctx = DummyContext()

    addressed, processed = await tb._addressed_and_processed_text(update, ctx)
    assert addressed is True
    assert processed == '5536604547'


@pytest.mark.asyncio
async def test_text_mention_detection():
    tb = build_test_bot()
    tb.bot_info = SimpleNamespace(username='mybot', id=999)

    entity = DummyEntity(type='text_mention', user=SimpleNamespace(id=999))
    msg = DummyMessage(text='hola bot 12345', entities=[entity])

    assert tb._is_mentioned_in_message(msg) is True
