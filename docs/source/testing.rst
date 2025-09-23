Testing
=======

Overview
--------

We cover the project with three categories of tests:

- **Unit tests**: located in ``tests/unit``.
- **Functional tests**: located in ``tests/functional``.
- **Integration tests**: located in ``tests/integration``.

How to run::

    pytest -v
    pytest tests/unit -v
    pytest tests/functional -v
    pytest tests/integration -v


Unit Tests
----------

.. automodule:: tests.unit.test_middleware
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: tests.unit.test_error_handlers
   :members:

Functional Tests
----------------

.. automodule:: tests.functional.test_auth
   :members:

.. automodule:: tests.functional.test_contacts
   :members:

Integration Tests
-----------------

.. automodule:: tests.integration.test_error_handlers_integration
   :members:
