How To Migrate to v1
====================

The ``v1`` release of ``pytest-lsp`` contains some breaking changes, mostly as a result of changes in the wider ecosystem.
This guide summarises the changes and provides references on where to get more details.

Python Support
--------------

This release removes support for Python 3.8 and adds support for Python 3.13.

``pytest``
----------

This release removes support for pytest ``v7``, if you have not done so already please update to pytest ``v8``.


``pytest-asyncio``
------------------

The minimum required version for ``pytest-asyncio`` is now ``0.24``, see `this guide <https://pytest-asyncio.readthedocs.io/en/latest/how-to-guides/migrate_from_0_23.html>`__ for details on upgrading

``pygls``
---------

``pygls``, the underlying language server protocol implementation used by ``pytest-lsp`` has been upgraded to ``v2``.
See `this guide <https://pygls.readthedocs.io/en/latest/howto/migrate-to-v2.html>`__ for details on the breaking changes this brings.
