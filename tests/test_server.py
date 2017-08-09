import pytest

from ethereumd.server import RPCServer

from .base import BaseTestRunner


class TestServer(BaseTestRunner):

    run_with_node = True

    @pytest.mark.asyncio
    async def test_call_server(self):
        # NOTE: Smoke call
        RPCServer()
