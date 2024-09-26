"""Rng device related test items
"""
from utils import STEPS, RESULT


def live_attach_rng_device(params, env):
    """
    Hotplug rng device to vm
    """
    params.doc_logger.info(STEPS + """Prepare rng device xml file
cat /tmp/rng.xml
<rng model='virtio'>
  <backend model='random'>/dev/urandom</backend>
</rng>
""")
    params.doc_logger.info("virsh attach-device %s /tmp/rng.xml --live" % params.guest_name)
    params.doc_logger.info(RESULT + "Device attached successfully")


def live_detach_rng_device(params, env):
    """
    Hot-unplug rng device from vm
    """
    params.doc_logger.info(STEPS + """Prepare rng device xml file
cat rng.xml
<rng model='virtio'>
  <backend model='random'>/dev/urandom</backend>
</rng>""")
    params.doc_logger.info("virsh detach-device %s rng.xml --live" % params.guest_name)
    params.doc_logger.info(RESULT + "Device detached successfully")


def verify_rng_in_vm(params, env):
    """
    Verify rng inside vm
    """
    params.doc_logger.info(STEPS + "Login guest and run command:")
    params.doc_logger.info("ls /dev/hwrng")
    params.doc_logger.info("/dev/hwrng")
    params.doc_logger.info("dd if=/dev/hwrng of=/dev/null count=2 bs=2")
    params.doc_logger.info(RESULT + "2+0 records in\n" +
                                    " 2+0 records out\n" +
                                    " 4 bytes copied, 0.00384156 s, 1.0 kB/s")
