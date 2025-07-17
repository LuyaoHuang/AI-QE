from depend_test_framework.test_object import Action, CheckPoint
from depend_test_framework.dependency import Provider, Consumer
from depend_test_framework.base_class import ParamsRequire


@Action.decorator(1)
@ParamsRequire.decorator(['guest_name', 'rng_model'])
@Consumer.decorator('$guest_name.active', Consumer.REQUIRE)
@Consumer.decorator('$guest_name.active.rng', Consumer.REQUIRE_N)
@Provider.decorator('$guest_name.active.rng', Provider.SET)
def live_attach_rng_device(params, env):
    """
    Hotplug rng device to vm
    """
    pass


@Action.decorator(1)
@ParamsRequire.decorator(['guest_name', 'rng_model'])
@Consumer.decorator('$guest_name.active.rng', Consumer.REQUIRE)
@Provider.decorator('$guest_name.active.rng', Provider.CLEAR)
def live_detach_rng_device(params, env):
    """
    Hot-unplug rng device from vm
    """
    pass


@CheckPoint.decorator(1)
@ParamsRequire.decorator(['guest_name'])
@Consumer.decorator('$guest_name.active.rng', Consumer.REQUIRE)
def verify_rng_in_vm(params, env):
    """
    Verify rng inside vm
    """
    pass
