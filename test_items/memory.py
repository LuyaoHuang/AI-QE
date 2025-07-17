from depend_test_framework.test_object import Action, CheckPoint
from depend_test_framework.dependency import Provider, Consumer
from depend_test_framework.base_class import ParamsRequire


@Action.decorator(1)
@ParamsRequire.decorator(['guest_name', 'curmem'])
@Consumer.decorator('$guest_name.active', Consumer.REQUIRE)
@Provider.decorator('$guest_name.active.curmem', Provider.SET)
def hot_set_guest_mem(params, env):
    pass


@Action.decorator(1)
@ParamsRequire.decorator(['guest_name', 'curmem'])
@Consumer.decorator('$guest_name.config', Consumer.REQUIRE)
@Provider.decorator('$guest_name.config.curmem', Provider.SET)
def cold_set_guest_mem(params, env):
    pass


@CheckPoint.decorator(1)
@ParamsRequire.decorator(['guest_name', 'curmem'])
@Consumer.decorator('$guest_name.active.curmem', Consumer.REQUIRE)
def verify_setmem_in_guest(params, env):
    pass
