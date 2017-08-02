from asynctest.mock import patch, CoroutineMock
import pytest

from ethereumd.poller import Poller, alertnotify

from .base import BaseTestRunner


class MockPoller(Poller):

    def __init__(self, blocknotify=None, walletnotify=None, alertnotify=None):
        cmds = {}
        if blocknotify:
            cmds['blocknotify'] = blocknotify
        if walletnotify:
            cmds['walletnotify'] = walletnotify
        if alertnotify:
            cmds['alertnotify'] = alertnotify
        self._cmds = cmds


class TestPoller(BaseTestRunner):

    run_with = ['node', 'proxy']

    @pytest.mark.asyncio
    async def test_alertnotify_valid_func_without_errors(self):
        class CorrectMockPoller(MockPoller):
            @alertnotify(exceptions=(Exception,))
            async def valid_func(self):
                pass

        poller = CorrectMockPoller()
        assert poller.has_alertnotify is False
        result = await poller.valid_func()
        assert result is None

    @pytest.mark.asyncio
    async def test_alertnotify_invalid_func_with_error_raise_no_notify(self):
        class IncorrectMockPoller(MockPoller):
            @alertnotify(exceptions=(Exception,))
            async def invalid_func(self):
                raise RuntimeError('Incorrect')

        poller = IncorrectMockPoller()
        assert poller.has_alertnotify is False

        with pytest.raises(RuntimeError) as excinfo:
            await poller.invalid_func()
        assert 'Incorrect' in str(excinfo)

    @pytest.mark.asyncio
    async def test_alertnotify_invalid_func_with_error_raise_and_notify(self):
        class IncorrectMockPoller(MockPoller):
            @alertnotify(exceptions=(RuntimeError,))
            async def invalid_func(self):
                raise RuntimeError('Incorrect')

        poller = IncorrectMockPoller(alertnotify='echo "%s"')
        assert poller.has_alertnotify is True

        with patch('asyncio.create_subprocess_exec') as sp_mock:
            process_mock = CoroutineMock()
            attrs = {'communicate.return_value': ('output', 'error')}
            process_mock.configure_mock(**attrs)
            sp_mock.return_value = process_mock
            await poller.invalid_func()

        assert sp_mock.call_count == 1
        assert process_mock.communicate.call_count == 1
