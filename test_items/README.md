# How to Write New Test Items

This guide explains how to create new test items for the depend test framework, following the established pattern seen in `vm_basic.py` and `vm_basic_doc.py`. Test items are composed of two main parts:

1.  **Dependency Definition (`*_basic.py`):** Defines the actions, their required parameters, and how they interact with system states and resources (dependencies). This file primarily uses decorators from `depend_test_framework`.
2.  **Documentation/Simulation (`*_basic_doc.py`):** Provides the human-readable steps and expected results for each action. This is used for generating test reports or simulating test execution.

---

## 1. Defining Test Actions and Dependencies (`your_module_name_basic.py`)

This file is crucial for the test framework to understand the structure, requirements, and effects of your test actions. You'll use classes and function decorators from `depend_test_framework.test_object` and `depend_test_framework.dependency`.

**Key Concepts and Decorators:**

*   **`@Action.decorator(priority)`**: Marks a function as a testable action. The `priority` (an integer) helps in determining the order or grouping of actions within the test plan.
*   **`@ParamsRequire.decorator(['param1', 'param2'])`**: Specifies the list of parameters (strings) that this action *must* receive in its `params` object to execute.
*   **`@Consumer.decorator('$resource.state', Consumer.REQUIRE_TYPE)`**: Declares that an action consumes or requires a certain state of a resource.
    *   `Consumer.REQUIRE`: The resource/state must exist.
    *   `Consumer.REQUIRE_N`: The resource/state must *not* exist.
    *   `$resource.state` is a string representing the resource, e.g., `'$guest_name.active'`, `'$disk_id.allocated'`.
*   **`@Provider.decorator('$resource.state', Provider.SET_TYPE)`**: Declares that an action provides or modifies a certain state of a resource.
    *   `Provider.SET`: The resource/state is set (e.g., created, activated).
    *   `Provider.CLEAR`: The resource/state is cleared (e.g., removed, deactivated).
*   **`@Graft.decorator('$resource.target', '$resource.source')`**: A concise way to declare that providing `$resource.source` also implies providing `$resource.target`. It essentially links the provision of one resource to another. For example, `@Graft.decorator('$guest_name.config', '$guest_name.active')` on a `start_guest` action means that if `guest_config` exists, starting the guest makes it `active`.
*   **`@Cut.decorator('$resource.state')`**: A concise way to declare that the action *clears* the specified resource. This is equivalent to `Provider('$resource.state', Provider.CLEAR)`. For example, `@Cut.decorator('$guest_name.active')` on a `destroy_guest` action means destroying the guest clears its active state.
*   **`TestObject` Class**: Use this for more complex test items that might need to dynamically add dependencies or have an object-oriented structure.
    *   **`_test_entry`**: A `set` that can hold initial `Action` and `ParamsRequire` declarations.
    *   **`__init__(self)`**: Use this method to dynamically add `Provider`, `Consumer`, `Graft`, or `Cut` declarations based on the object's initialization.
    *   **`__call__(self, params, env)`**: This is the method that the framework "calls" when executing the test item. Often, for dependency definition files, this method simply contains `pass`, as the actual system interaction logic might reside elsewhere in the test framework or external modules.

---

**Example (`test_items/vm_basic.py`):**

```python
# ... existing imports ...
from depend_test_framework.test_object import Action, TestObject
from depend_test_framework.dependency import Provider, Consumer, Graft, Cut
from depend_test_framework.base_class import ParamsRequire

# Example: A simple function-based action
@Action.decorator(1)
@ParamsRequire.decorator(['guest_name'])
@Consumer.decorator('$guest_name.active', Consumer.REQUIRE_N) # Requires guest to not be active
@Consumer.decorator('$guest_name.config', Consumer.REQUIRE)   # Requires guest config to exist
@Graft.decorator('$guest_name.config', '$guest_name.active') # Starting implies active if config exists
def start_guest(params, env):
    """
    Start guest
    """
    pass # Actual execution logic is typically handled by the framework

# Example: A class-based action
class define_guest(TestObject):
    """ Define guest """
    _test_entry = set([Action(1),
                       ParamsRequire(['guest_name', 'guest_xml'])])

    def __init__(self):
        # Dynamically add a provider: defining a guest provides its configuration
        self._test_entry.add(Provider('$guest_name.config', Provider.SET))

    def __call__(self, params, env):
        pass # Actual execution logic is typically handled by the framework
```

---

**Steps to Create a New `your_module_name_basic.py` entry:**

1.  **Choose a structure:** Decide if your test item will be a standalone function or a `TestObject` class. Functions are simpler for direct actions, while `TestObject` classes are suitable for actions with more complex or dynamic dependency setups.
2.  **Apply `@Action.decorator(priority)`**: Give your action a logical priority.
3.  **Define Parameter Requirements**: Use `@ParamsRequire.decorator(['param_name'])` to list all necessary input parameters.
4.  **Declare Consumers**: What preconditions must be met? Use `@Consumer.decorator` to specify required (`Consumer.REQUIRE`) or non-required (`Consumer.REQUIRE_N`) resource states.
5.  **Declare Providers**: How does your action change the system state? Use `@Provider.decorator`, `@Graft.decorator`, or `@Cut.decorator` to declare which resources are set or cleared. `Graft` and `Cut` are preferred for their conciseness.

---

## 2. Documenting Test Actions (`your_module_name_basic_doc.py`)

This file provides human-readable output for each action, which is invaluable for generating test reports or simulating test runs without actually executing system commands.

**Key Concepts:**

*   **Mirroring Function Names**: For every action defined in `your_module_name_basic.py`, there should be a corresponding function with the exact same name in this file.
*   **`params.doc_logger.info()`**: This method is used to log information to the documentation output.
    *   `STEPS`: A constant (imported from `utils`) used to prefix log messages describing the actions being taken.
    *   `RESULT`: A constant (imported from `utils`) used to prefix log messages describing the expected outcome or result.
*   **Using `params`**: Access action-specific parameters (e.g., `params.guest_name`, `params.guest_xml`) to create dynamic and informative log messages.

---

**Example (`test_items/vm_basic_doc.py`):**

```python
# ... existing imports ...
from utils import STEPS, RESULT

def start_guest(params, env):
    """
    Start a guest
    """
    params.doc_logger.info(STEPS + "# virsh start %s" % params.guest_name)
    params.doc_logger.info(RESULT + "Domain %s started" % params.guest_name)

def define_guest(params, env):
    """
    Define a new guest
    """
    params.doc_logger.info(STEPS + "# virsh define %s" % params.guest_xml)
    params.doc_logger.info(RESULT + "Domain %s defined from %s" % (params.guest_name,
                                                                   params.guest_xml))
```

---

**Steps to Create a New `your_module_name_basic_doc.py` entry:**

1.  **Create a function** that has the **exact same name** as the corresponding action defined in `your_module_name_basic.py`.
2.  **Add a clear docstring** to describe the action.
3.  **Use `params.doc_logger.info()`** to log the simulated steps and expected results.
    *   Prefix steps with `STEPS + ` (e.g., `STEPS + "# Command to execute"`).
    *   Prefix results with `RESULT + ` (e.g., `RESULT + "Expected outcome"`).
    *   Use the parameters available in the `params` object to make the messages specific and useful (e.g., `params.guest_name`).

---