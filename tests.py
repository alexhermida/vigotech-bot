from unittest.mock import Mock, patch

import pytest
from telegram import Bot
from telegram.ext import Updater

from bot import MESSAGES, reply_message


@pytest.fixture(scope='function')
def updater():
    up = Updater(bot=Bot('123:zyxv'))
    yield up
    if up.running:
        up.stop()


@patch('settings.TELEGRAM_ADMINS_LIST', [1])
def test_reply_message(updater):
    response = reply_message('start')

    update = Mock(effective_user=Mock(id=1), message=Mock())
    next_step = response(updater.bot, update=update)

    assert not next_step
