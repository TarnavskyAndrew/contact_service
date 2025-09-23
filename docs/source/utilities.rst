Utilities
=========

Standalone helper scripts for administration, debugging, and testing.

.. .. contents::
..    :local:
..    :depth: 1

check_smtp.py
-------------
Test SMTP connection and send a test email.

.. automodule:: check_smtp
   :members:
   :undoc-members:
   :show-inheritance:

Usage example::

   poetry run python check_smtp.py


parse_jwt.py
------------
Decode and inspect JWT tokens. Detects type (access, refresh,
email verification, password reset) and expiration time.

.. automodule:: parse_jwt
   :members:
   :undoc-members:
   :show-inheritance:

Usage example::

   poetry run python parse_jwt.py


seed.py
-------
Create the initial administrator user in the database.

.. automodule:: seed
   :members:
   :undoc-members:
   :show-inheritance:

Usage example::

   poetry run python seed.py
