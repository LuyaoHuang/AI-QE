"""VM memory related test items
"""
from utils import STEPS, RESULT, SETUP


def hot_set_guest_mem(params, env):
    """
    Use virsh setmem to change the running guest memory size
    """
    params.doc_logger.info(STEPS + "# virsh setmem %s %d --live" % (params.guest_name, params.curmem))
    params.doc_logger.info(RESULT)


def cold_set_guest_mem(params, env):
    """
    Use virsh setmem to change the guest memory size in xml
    """
    params.doc_logger.info(STEPS + "# virsh setmem %s %d --config" % (params.guest_name, params.curmem))
    params.doc_logger.info(RESULT)


def verify_setmem_in_guest(params, env):
    """
    Check the current memory size in the guest
    """
    params.doc_logger.info(STEPS + "# cat /proc/meminfo | grep MemTotal")
    params.doc_logger.info(RESULT + "MemTotal:        %d kB" % params.curmem)
