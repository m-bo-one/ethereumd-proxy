from asynctest.mock import patch, CoroutineMock
import pytest

from ethereumd.poller import Poller, alertnotify
from ethereumd.proxy import RPCProxy

from .base import BaseTestRunner
from .fakers import fake_call


class FakePoller(Poller):

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

    run_with = ['proxy', 'poller']

    @pytest.mark.asyncio
    async def test_alertnotify_valid_func_without_errors(self):
        class CorrectFakePoller(FakePoller):
            @alertnotify(exceptions=(Exception,))
            async def valid_func(self):
                pass

        poller = CorrectFakePoller()
        assert poller.has_alertnotify is False
        result = await poller.valid_func()
        assert result is None

    @pytest.mark.asyncio
    async def test_alertnotify_invalid_func_with_error_raise_no_notify(self):
        class IncorrectFakePoller(FakePoller):
            @alertnotify(exceptions=(Exception,))
            async def invalid_func(self):
                raise RuntimeError('Incorrect')

        poller = IncorrectFakePoller()
        assert poller.has_alertnotify is False

        with pytest.raises(RuntimeError) as excinfo:
            await poller.invalid_func()
        assert 'Incorrect' in str(excinfo)

    @pytest.mark.asyncio
    async def test_alertnotify_invalid_func_with_error_raise_and_notify(self):
        class IncorrectFakePoller(FakePoller):
            @alertnotify(exceptions=(RuntimeError,))
            async def invalid_func(self):
                raise RuntimeError('Incorrect')

        poller = IncorrectFakePoller(alertnotify='echo "%s"')
        assert poller.has_alertnotify is True

        with patch('asyncio.create_subprocess_exec') as sp_mock:
            process_mock = CoroutineMock()
            attrs = {'communicate.return_value': ('output', 'error')}
            process_mock.configure_mock(**attrs)
            sp_mock.return_value = process_mock
            await poller.invalid_func()

        assert sp_mock.call_count == 1
        assert process_mock.communicate.call_count == 1

    @pytest.mark.asyncio
    async def test_call_blocknotify_and_has_block(self):
        with patch('ethereumd.poller.Poller.poll'):
            poller = Poller(self.proxy, cmds={'blocknotify': 'echo "%s"'})
        with patch.object(RPCProxy, '_call', side_effect=fake_call()):
            with patch.object(Poller, '_exec_command',
                              side_effect=lambda x, y: None) as exec_mock:
                assert exec_mock.call_count == 0
                await poller.blocknotify()
                assert exec_mock.call_count == 1

    @pytest.mark.asyncio
    async def test_call_blocknotify_and_has_no_block(self):
        with patch('ethereumd.poller.Poller.poll'):
            poller = Poller(self.proxy, cmds={'blocknotify': 'echo "%s"'})
        with patch.object(RPCProxy, '_call',
                          side_effect=fake_call(['-eth_getFilterChanges'])):
            with patch.object(Poller, '_exec_command',
                              side_effect=lambda x, y: None) as exec_mock:
                assert exec_mock.call_count == 0
                await poller.blocknotify()
                assert exec_mock.call_count == 0

    @pytest.mark.asyncio
    async def test_call_walletnotify_and_has_trans(self):
        with patch('ethereumd.poller.Poller.poll'):
            poller = Poller(self.proxy, cmds={'walletnotify': 'echo "%s"'})
        with patch.object(RPCProxy, '_call', side_effect=fake_call()):
            with patch.object(Poller, '_exec_command',
                              side_effect=lambda x, y: None) as exec_mock:
                assert exec_mock.call_count == 0
                await poller.walletnotify()
                assert exec_mock.call_count == 1

    @pytest.mark.asyncio
    async def test_call_walletnotify_and_has_no_trans(self):
        with patch('ethereumd.poller.Poller.poll'):
            poller = Poller(self.proxy, cmds={'walletnotify': 'echo "%s"'})
        with patch.object(RPCProxy, '_call',
                          side_effect=fake_call(['-eth_getFilterChanges'])):
            with patch.object(Poller, '_exec_command',
                              side_effect=lambda x, y: None) as exec_mock:
                assert exec_mock.call_count == 0
                await poller.walletnotify()
                assert exec_mock.call_count == 0

    @pytest.mark.asyncio
    async def test_method_has_command(self):
        with patch('ethereumd.poller.Poller.poll'):
            poller = Poller(self.proxy)
            assert poller.has_blocknotify is False
            assert poller.has_walletnotify is False
            assert poller.has_alertnotify is False

            poller = Poller(self.proxy, cmds={'blocknotify': 'echo "%s"'})
            assert poller.has_blocknotify is True
            assert poller.has_walletnotify is False
            assert poller.has_alertnotify is False

            poller = Poller(self.proxy, cmds={'walletnotify': 'echo "%s"'})
            assert poller.has_blocknotify is False
            assert poller.has_walletnotify is True
            assert poller.has_alertnotify is False

            poller = Poller(self.proxy, cmds={'alertnotify': 'echo "%s"'})
            assert poller.has_blocknotify is False
            assert poller.has_walletnotify is False
            assert poller.has_alertnotify is True

            poller = Poller(self.proxy, cmds={'blocknotify': 'echo "%s"',
                                              'walletnotify': 'echo "%s"',
                                              'alertnotify': 'echo "%s"'})
            assert poller.has_blocknotify is True
            assert poller.has_walletnotify is True
            assert poller.has_alertnotify is True

    @pytest.mark.asyncio
    async def test_method__is_account_trans_and_trans_exists(self):
        with patch('ethereumd.poller.Poller.poll'):
            poller = Poller(self.proxy)

        with patch.object(RPCProxy, '_call', side_effect=fake_call()):
            txid = '0x9c864dd0e7fdcfb3bd7197020ac311cbacef1aa29b49791223427bbedb6d36ad'
            is_account_trans = await poller._is_account_trans(txid)
        assert is_account_trans is True

    @pytest.mark.asyncio
    async def test_method__is_account_trans_and_trans_not_exists(self):
        with patch('ethereumd.poller.Poller.poll'):
            poller = Poller(self.proxy)

        with patch.object(RPCProxy, '_call', side_effect=fake_call('-')):
            txid = '0x9c864dd0e7fdcfb3bd7197020ac311cbacef1aa29b49791223427bbedb6d36ad'
            is_account_trans = await poller._is_account_trans(txid)
        assert is_account_trans is False

    @pytest.mark.asyncio
    async def test_method__build_filter_which_exists(self):
        with patch('ethereumd.poller.Poller.poll'):
            poller = Poller(self.proxy)

        with patch.object(RPCProxy, '_call', side_effect=fake_call()):
            # latest filter for blocks
            assert hasattr(poller, '_latest') is False, \
                'Poller must not have here _latest attr'
            await poller._build_filter('latest')
            assert hasattr(poller, '_latest') is True, \
                'Poller must have here _latest attr'

            # pending filter for transacs
            assert hasattr(poller, '_pending') is False, \
                'Poller must not have here _pending attr'
            await poller._build_filter('pending')
            assert hasattr(poller, '_pending') is True, \
                'Poller must have here _pending attr'

    @pytest.mark.asyncio
    async def test_method__build_filter_which_not_exists(self):
        with patch('ethereumd.poller.Poller.poll'):
            poller = Poller(self.proxy)

        with patch.object(RPCProxy, '_call', side_effect=fake_call('-')):
            with pytest.raises(KeyError) as excinfo:
                await poller._build_filter('doesnotexists')
            assert 'doesnotexists' in str(excinfo)
