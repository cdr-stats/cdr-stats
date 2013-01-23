.. _configuration-acl-control:

ACL Control
===========

One of the benefits of CDR-Stats is ACL access, allowing numerous people to
access CDR-Stats each viewing their own CDR with permissions assigned to allow
viewing different parts of the interface.

Add Customer
------------

To add a new user, enter the admin screen and Add Customer. Enter a username
and password, (twice for authentication), optionally add address details, then
enter the accountcode of the customer which corresponds to the accountcode
that is delivered in the CDR. When done, click save, and the customer details
will be saved and the page reloaded and now displays the user permissions
available.

Permissions can be added individually by selecting the permission and then
pressing the right arrow to  move the permission from the left field to the
right field. When done, click save. The permissions to assign to the user are
those beginning with user_profile and cdr_alert.

Group Permissions
-----------------

When you have many customers who are all to have the same permissions, you
can add a group, assign the group the desired permissions, then add the
customer to the group.

From the admin screens, Click add group, give it a name, assign permissions
then save. Finally edit the customer, select the groups to which the customer
will belong, then click save. The customer will then inherit permissions from
their group.
