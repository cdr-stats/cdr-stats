.. _mongodb:

MongoDB
=======

:Web: http://www.mongodb.org/
:Download: http://www.mongodb.org/downloads/

--


MongoDB is a scalable, high-performance, document-oriented schemaless
database, everything in MongoDB is a document. There is no notion of a rigid table
structure composed of columns and types.

Instead of storing your data in tables and rows as you would with a relational database,
in MongoDB you store JSON-like documents with dynamic schemas. The goal of MongoDB is
to bridge the gap between key-value stores (which are fast and scalable) and relational
databases (which have rich functionality).


.. contents::
    :local:
    :depth: 1

.. _why_mongodb:

Why MongoDB
-----------

Why did we choose MongoDB and what are the benefits?
To answer this questions I think we should enumerate some of the major features of MongoDB.

**Document-oriented**:
    * Documents (objects) map well to programming language data types
    * Embedded documents and arrays reduce need for joins
    * Dynamically-typed (schema-less) for easy schema evolution

**High performance**:
    * No joins and embedding make reads and writes fast
    * Indexes including indexing of keys from embedded documents and arrays

**High availability**:
    * Replicating servers with automatic master failover


A more detailed list of everything provided by mongoDB can be found at
http://www.mongodb.org/display/DOCS/Introduction

As MongoDB is a Document-oriented datastore, it had a potential to store a huge
number of CDR's, Call Detail Record formats vary between Telecom Switch types.
For these reasons a NoSQL database is a very good candidate for a CDR warehouse.


.. _datastore_architecture:

Datastore Architecture
----------------------

The MongoDB aggregation framework provides a means to calculate aggregate
values without having to use Map-reduce (http://www.mongodb.org/display/DOCS/MapReduce).
For those familiar with SQL, the aggregation framework can be used to do
the kind of thing that SQL does with group-by and distinct, as well as
some simple forms of self-joins.

The aggregation framework also provides projection facilities that can be
used to reshape data. This includes the ability to add computed fields, to
create new virtual sub-objects, and to extract sub-fields and bring them to
the top-level of results.

**update()** replaces the document matching criteria entirely with objNew.

Shell syntax for update(): db.collection.update(criteria, objNew, upsert, multi)

Arguments:
    * **criteria** - query which selects the record to update
    * **objNew** - updated object or $ operators (e.g., $inc) which manipulate the object
    * **upsert** - if this should be an "upsert" operation; that is, if the record(s) do not exist, insert one. Upsert only inserts a single document.
    * **multi** - indicates if all documents matching criteria should be updated rather than just one. Can be useful with the $ operators below.


Shell syntax for $inc: { $inc : { field : value } }
Increments “field” by the number “value” if “field” is present in the object,
otherwise sets “field” to the number “value”. This can also be used to
decrement by using a negative “value”.

.. _pre_aggregated_reports:

Pre-Aggregated Reports
----------------------
If you collect a large amount of data and you want to have access to aggregated information
and reports, then you need a method to aggregate these data into a usable form.
Pre-aggregating your data will provide  performance gains when you try to retrieve
that aggregrate information in realtime.

MongoDB is an engine is used for collecting and processing events in real time for use
in generating up to the minute or second reports.

The first step in the aggregation process is to aggregate event data into the finest required
granularity. Then use this aggregation to generate the next least specific level granularity
and this repeat process until you have generated all required views.

.. _one_doc__per_day:

One Document Per Day
--------------------

Consider the following example schema for a solution that stores in a single document all
statistics of a page for one day::

    {
        _id: "20101010/site-1/apache_pb.gif",
        metadata: {
            date: ISODate("2000-10-10T00:00:00Z"),
            site: "site-1",
            page: "/apache_pb.gif" },
        daily: 5468426,
        hourly: {
            "0": 227850,
            "1": 210231,
            ...
            "23": 20457 },
        minute: {
            "0": 3612,
            "1": 3241,
            ...
            "1439": 2819 }
    }

This approach has a couple of advantages:

    * For every request on the website, you only need to update one document.
    * Reports for time periods within the day, for a single page require fetching a single document.

There are, however, significant issues with this approach. The most significant issue is that,
as you ``upsert`` data into the hourly and monthly fields, the document grows. Although MongoDB will
pad the space allocated to documents, it will need to reallocate these documents multiple times
throughout the day, which impacts performance.

.. _separate_doc_by_granularity_level:

Separate Documents by Granularity Level
---------------------------------------

Pre-allocating documents is a reasonable design for storing intra-day data, but the model breaks
down when displaying data over longer multi-day periods like months or quarters. In these cases,
consider storing daily statistics in a single document as above, and then aggregate monthly data
into a separate document.

This introduce a second set of upsert operations to the data collection and aggregation portion of
your application but the gains reduction in disk seeks on the queries, should be worth the costs.
Consider the following example schema:

**Daily Statistics**::

    {
        _id: "20101010/site-1/apache_pb.gif",
        metadata: {
            date: ISODate("2000-10-10T00:00:00Z"),
            site: "site-1",
            page: "/apache_pb.gif" },
        hourly: {
            "0": 227850,
            "1": 210231,
            ...
            "23": 20457 },
        minute: {
            "0": {
                "0": 3612,
                "1": 3241,
                ...
                "59": 2130 },
            "1": {
                "0": ...,
            },
            ...
            "23": {
                "59": 2819 }
        }
    }

**Monthly Statistics**::

    {
        _id: "201010/site-1/apache_pb.gif",
        metadata: {
            date: ISODate("2000-10-00T00:00:00Z"),
            site: "site-1",
            page: "/apache_pb.gif" },
        daily: {
            "1": 5445326,
            "2": 5214121,
            ... }
    }

To read more about Pre-Aggregated data with MongoDB, please refer to mongoDB documentation:

- http://docs.mongodb.org/manual/use-cases/pre-aggregated-reports/

- http://docs.mongodb.org/manual/use-cases/hierarchical-aggregation/


.. _preaggregate_designpattern_call_data:

Preaggregate Design Pattern with Call Data
------------------------------------------

We explained previously why preaggregating is a huge performance gain for analytic reporting and how it reduces disk seeks on your
aggregate queries, we will now show how we apply this pattern to our call data.

Our data are the CDR (Call Detail Records) which are pre-processed for type validation, after this sanitisation of the call data, we proceed to the pre=aggragation step. For this we create a new daily_cdr collection which is aggregated daily.

Our code with PyMongo::

    DAILY_ANALYTIC.update(
            {
            "_id": id_daily,
            "metadata": {
                "date": d,
                "switch_id": switch_id,
                "country_id": country_id,
                "accountcode": accountcode,
                "hangup_cause_id": hangup_cause_id,
                },
            },
            {
            "$inc": {
                "call_daily": 1,
                "call_hourly.%d" % (hour,): 1,
                "call_minute.%d.%d" % (hour, minute,): 1,
                "duration_daily": duration,
                "duration_hourly.%d" % (hour,): duration,
                "duration_minute.%d.%d" % (hour, minute,): duration,
                }
        }, upsert=True)

The '_id' is created with concatenation of the day, switch, country, accountcode and hangup cause ID.

The above collection is very fast to query, to retrieve the amount of calls for a day for a specific accountcode will be immediate.
The field call_hourly can be used to plot the calls per hour for a single user or for a specific country.


.. _cdr_stats_mongodb_collection:

CDR-Stats MongoDB Collections
-----------------------------

**1) cdr_common:**
    To collect all CDR's from different switches & store into one common format which include the following fields
    switch_id,  caller_id_number, caller_id_name, destination_number, duration, billsec, hangup_cause_id, accountcode, direction, uuid, remote_media_ip, start_uepoch, answer_uepoch, end_uepoch, mduration,
    billmsec, read_codec, write_codec, cdr_type, cdr_object_id, country_id, authorized.
    This cdr_common collection used to view cdr records on customer panel

**2) monthly_analytic:**
    To collect monthly analytics from CDR's which include following fields
    date, country_id, accountcode, switch_id, calls, duration.
    This monthly_analytic collection is used to view monthly graph on customer panel

**3) daily_analytic:**
    To collect daily analytics from CDR's which include following fields date,
    hangup_cause_id, country_id, accountcode, switch_id, calls, duration.
    This daily_analytic collection used to view daily graph/hourly graph on customer panel.

**4) concurrent_call:**
    To collect concurrent calls which include following fields
    switch_id, call_date, numbercall, accountcode.
    This concurrent_call collection is used to view concurrent call real-time graph on customer panel


.. image:: ./_static/images/CDR-Stats-MongoDB.png
    :width: 600

