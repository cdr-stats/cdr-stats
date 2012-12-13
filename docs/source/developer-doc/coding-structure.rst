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
    |   `-- api_playground
    |-- cdr                - The code for CDR
    |   |-- management
    |   |-- templatetags
    |   `-- fixtures
    |-- cdr_alert          - The code for alarm, blacklist, whitelist
    |   |-- management
    |   `-- fixtures
    |-- frontend           - The code for login, logout user
    |-- user_profile       - The code for user detail of system
    |-- static
    |   |-- cdr
    |   |    |-- css
    |   |    |-- js
    |   |    |-- icons
    |   |    `-- images
    |-- resources          - This area is used to hold media files
    `-- templates          - This area is used to override templates
        |-- admin
        |-- admin_tools
        |-- api_browser
        `-- frontend
