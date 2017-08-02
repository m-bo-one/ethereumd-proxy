from ethereumd.utils import (
    hex_to_dec, wei_to_ether, ether_to_wei, ether_to_gwei)

from .base import BaseTestRunner


class TestUtils(BaseTestRunner):

    def test_hex_to_dec(self):
        result = hex_to_dec('-0x8')  # -8
        assert result == -8
        result = hex_to_dec('0x0')  # 0
        assert result == 0
        result = hex_to_dec('0x10')  # 16
        assert result == 16

    def test_wei_to_ether(self):
        """Test convertion wei to ether (it is 10 in -18 step).
        """
        result = wei_to_ether(10 ** 18)
        assert result == 1  # 1 ether
        result = wei_to_ether(1)
        assert result == 10 ** -18  # 1 in -18 step ether

    def test_ether_to_wei(self):
        """Test convertion ether to wei (it is 10 in 18 step).
        """
        result = ether_to_wei(1)
        assert result == 10 ** 18  # 10 in 18 step wei
        result = ether_to_wei(10 ** -18)
        assert result == 1  # 1 wei

    def test_ether_to_gwei(self):
        """Test convertion ether to gwei (it is 10 in 9 step).
        """
        result = ether_to_gwei(1)
        assert result == 10 ** 9  # 10 in 9 step Gwei
        result = ether_to_gwei(10 ** -9)
        assert result == 1  # 1 Gwei
