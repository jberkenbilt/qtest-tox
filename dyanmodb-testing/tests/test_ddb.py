from __future__ import print_function
import os
import pytest
from ddb.ddb import Metadata

use_moto = True if os.getenv('USE_MOTO') else False  # duplicated


# The fixtures are set up so that each "class" gets a coherent
# dynamodb environment that stays intact throughout the duration of
# the class. Class-scoped fixtures are reset for each method that is
# not in a class. This allows creation of tests that accumulate state.
# While such tests have the drawback of not being callable
# independently, they are an important way to test the behavior of
# something when it is used in that way.

@pytest.fixture
def m(dynamodb_resource_options, table_name):
    return Metadata(table_name,
                    dynamodb_resource_options=dynamodb_resource_options)

def test_no_conditions(m):
    assert m.add_new('0', 'zero')
    assert m.get_all() == [{'key': '0', 'value': 'zero'}]
    assert m.update('0', 'one', 'zero')
    assert m.get_all() == [{'key': '0', 'value': 'one'}]
    assert m.delete('0', 'one')
    assert m.get_all() == []

def test_add_new(m):
    assert m.add_new('1', 'one')
    assert m.get_all() == [{'key': '1', 'value': 'one'}]

def test_add_new_again(m):
    # The fact that this passes when the previous test passes shows
    # that this method gets a fresh dynamodb environment and does not
    # see affects of the previous one.
    assert m.get_all() == []
    assert m.add_new('1', 'one')
    assert m.get_all() == [{'key': '1', 'value': 'one'}]

# State in dynamodb accumulates through all the tests a class. While
# this means earlier failures may invalidate later tests, it makes it
# possible to write discrete tests for behavior in non-initial states
# without having to repeat the accumulating setup for each test. This
# can be important for testing the way things work in actual
# production.
class Test1:
    def test_starts_empty(self, m):
        assert m.get_all() == []

    def test_add_new(self, m):
        assert m.add_new('1', 'one')
        assert m.get_all() == [{'key': '1', 'value': 'one'}]

    @pytest.mark.xfail(condition="use_moto", strict=True)
    def test_add_new_exists(self, m):
        # The fact that the first add_new call here returns false
        # shows that the current dynamodb environment persists
        # throughout the class, so changes to it from earlier test
        # methods in this class persist.
        assert not m.add_new('1', 'one')
        assert not m.add_new('1', 'one')

    @pytest.mark.xfail(condition="use_moto", strict=True)
    def test_update(self, m):
        assert not m.update('1', 'two', 'two')
        assert m.update('1', 'two', 'one')
        assert m.get_all() == [{'key': '1', 'value': 'two'}]

    @pytest.mark.xfail(condition="use_moto", strict=True)
    def test_delete(self, m):
        assert m.add_new('2', 'three')
        assert m.get_all() == [{'key': '1', 'value': 'two'},
                               {'key': '2', 'value': 'three'}]
        assert not m.delete('2', 'two')
        assert m.delete('2', 'three')
        assert m.get_all() == [{'key': '1', 'value': 'two'}]
        assert not m.delete('2', 'three')
        assert m.get_all() == [{'key': '1', 'value': 'two'}]
