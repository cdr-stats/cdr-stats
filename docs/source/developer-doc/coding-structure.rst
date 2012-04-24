.. _coding-structure:


Coding Style & Structure
========================

-----
Style
-----

Coding follows the `PEP 8 Style Guide for Python Code <http://www.python.org/dev/peps/pep-0008/>`_.

---------
Structure
---------

The CDR-Stats directory::
    

    |-- api                - The code for APIs
    |-- cdr                - The code for CDR
    |   `-- fixtures
    |-- cdr_alert
    |-- static
    |   |-- cdr
    |   |    |-- css
    |   |    |-- js
    |   |    |-- icons
    |   |    `-- images
    |-- resources          - This area is used to hold media files
    `-- templates          - This area is used to override templates
        |-- admin
        `-- cdr
