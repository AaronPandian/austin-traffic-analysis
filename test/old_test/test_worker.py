import pytest
import redis
import json

from hotqueue import HotQueue
from ..src.worker import do_work

test_jid = '12535'

def test_worker():
    assert isinstance(do_work(test_jid), None) == True
