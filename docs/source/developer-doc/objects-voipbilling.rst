.. _object-description:

=======================================
Objects used by the VoIP Billing module
=======================================

.. _object-prefix:

Prefix
======

These are the prefixes and destinations.
For instance, 44 ; United Kingdom


.. _object-provider:

Provider
========

This defines the VoIP Provider you want to use to deliver your VoIP calls.
Each provider will be associated to a Gateway which will link to the Service
Provider.


.. _object-voipplan:

VoIPPlan
========

VoIPPlans are associated to your clients, this defines the rate at which the
VoIP calls are sold to your clients. A VoIPPlan is a collection of
VoIPRetailPlans, you can have 1 or more VoIPRetailPlans associated to the
VoIPPlan.

* A client has a single VoIPPlan
* A VoIPPlan has many VoIPRetailPlans
* A VoIPRetailPlan has VoIPRetailRates

The LCR system will route the VoIP via the lowest cost carrier.


.. _object-voipretailplan:

VoIPRetailPlan
==============

This contains the `VoIPRetailRates`, the list of rates to retail to the customer.
These plans are associated to the VoIPPlan with a ManyToMany relation.

It defines the costs at which we sell the VoIP calls to the clients.
VoIPRetailPlan will then contain a set of VoIPRetailRates which will define the
cost of sending a VoIP to each destination.

The system can have several VoIPRetailPlans, but only the ones associated to the
VoIPplan will be used by the client.


.. _object-voipplan-voipretailplan:

VoIPPlan_VoIPRetailPlan
=======================

Help to setup the `ManytoMany` relationship between VoIPPlan & VoIPRetailPlan.


.. _object-voipretailrate:

VoIPRetailRate
==============

A single VoIPRetailRate consist of a retail rate and prefix at which you want
to use to sell a VoIP to a particular destination.
VoIPRetailRates are grouped by VoIPRetailPlan, which will be then in turn be
associated to a VoIPPlan.


.. _object-voipcarrierplan:

VoIPCarrierPlan
===============

Once the retail price is defined by the VoIPRetailPlan, we also need to know
which is the best route to send the call, what will be our cost, and which
Gateway/Provider will be used.

VoIPCarrierPlan is linked to the VoIPRetailPlan, so once we found how to sell the
service to the client we need to look at which carrier (Provider) we want to use.
The VoIPCarrierPlan defines exactly this.

The system can have several VoIPCarrierPlans, but only the one associated to the
VoIPRetailPlan-VoIPPlan will be used to connect the VoIP of the client.


.. _object-voipcarrierrate:

VoIPCarrierRate
===============

The VoIPCarrierRates are a set of all the carrier rate and prefix that will be
used to purchase the VoIP from your carrier, VoIPCarrierRates are grouped by
VoIPCarrierPlan, which will be then associated to a VoIPRetailPlan.


.. _object-voipplan-voipcarrierplan:

VoIPPlan_VoIPCarrierPlan
========================

Help to setup the `ManytoMany` relationship between VoIPPlan & VoIPCarrierPlan.


.. _object-voip-call-report:

VoIP Call Report
================

This gives information of all the call delivered with the carrier charges and
revenue of each message.
