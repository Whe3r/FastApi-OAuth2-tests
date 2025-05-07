import unittest.mock
from unittest.mock import MagicMock, Mock

mock = Mock(side_effect=KeyError('foo'))
values = {'a': 1, 'b': 2, 'c': 3}


def side_effect(arg):
    return values[arg]

mock.side_effect = side_effect
print(mock('a'), mock('b'), mock('c'))
mock.side_effect = [5, 4, 3, 2, 1]
print(mock(), mock(), mock())