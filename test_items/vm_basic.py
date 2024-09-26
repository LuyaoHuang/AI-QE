from depend_test_framework.test_object import Action, CheckPoint, TestObject, Mist, MistDeadEndException, MistClearException
from depend_test_framework.dependency import Provider, Consumer, Graft, Cut
from depend_test_framework.base_class import ParamsRequire


PARAM = {}
ENV = {}


@Action.decorator(1)
@ParamsRequire.decorator(['guest_name'])
@Consumer.decorator('$guest_name.active', Consumer.REQUIRE_N)
@Consumer.decorator('$guest_name.config', Consumer.REQUIRE)
# @Provider.decorator('$guest_name.active', Provider.SET)
@Graft.decorator('$guest_name.config', '$guest_name.active')
def start_guest(params, env):
    """
    Start guest
    """
    pass


@Action.decorator(1)
@ParamsRequire.decorator(['guest_name'])
@Consumer.decorator('$guest_name.active', Consumer.REQUIRE)
# @Provider.decorator('$guest_name.active', Provider.CLEAR)
@Cut.decorator('$guest_name.active')
def destroy_guest(params, env):
    """
    Destroy guest
    """
    pass


class define_guest(TestObject):
    """ define guest"""
    _test_entry = set([Action(1),
                       ParamsRequire(['guest_name', 'guest_xml'])])
    def __init__(self):
        self._test_entry.add(Provider('$guest_name.config', Provider.SET))

    def __call__(self, params, env):
        pass


class undefine_guest(TestObject):
    """undefine guest"""
    _test_entry = set([Action(1),
                       ParamsRequire(['guest_name'])])
    def __init__(self):
        self._test_entry.add(Consumer('$guest_name.config', Consumer.REQUIRE))
#        self._test_entry.add(Provider('$guest_name.config', Provider.CLEAR))
        self._test_entry.add(Cut('$guest_name.config'))

    def __call__(self, params, env):
        pass
