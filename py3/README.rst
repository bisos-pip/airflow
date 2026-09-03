==============================================================================
bisos.airflow: Apache Airflow platform management via BISOS Capability Bundles
==============================================================================

.. contents::
   :depth: 3
..

Overview
========

*bisos.airflow* is a BISOS package for managing an Apache Airflow
platform — webserver (API server), scheduler, triggerer, metadata
database, and DAG development/testing — as a BISOS Capability Bundle
(CBS/CBM) of ``systemd``-planted Command Services.

With CBM (Capability Bundle Materialization), Airflow's four processes
are installed as independent host ``systemd`` units rather than one
monolithic ``airflow standalone`` process: a planted pointer leaf
(``cbmProc.spcs``) subprocess-invokes a Capability Bundle Specification
(``airflow-cbs.pcs``) which declares package installation (sbom), the
four ``systemd`` units, and the assembly step needed to bring up a
working ``airflow.here`` installation on a single host. This gives
independent start/stop/status and independent logs per role, without the
operational overhead of a distributed executor (Celery/Kubernetes) or
containers.

Package Documentation At Github
===============================

The information below is a subset of the full of documentation for this
bisos-pip package. More complete documentation is available at:
https://github.com/bisos-pip/airflow-cs

Capability Materialization
==========================

The figure below shows the top-down layering of ``airflow.here``'s
Capability Materialization: the planted CBM pointer leaf
(``/bisos/platform/sys/cbm/collective/hereWeb/airflow/cbmProc.spcs``)
points to (and does **not** duplicate) the CBS
(``py3/bin/airflow-cbs.pcs``), which declares the bundle of
``airflow-sbom.pcs``, the 4 ``airflow-*-sysd.pcs`` units, and
``airflow-assemble.cs``. ``py3/bin/airflowAdmin.cs`` sits below all of
that as the day-to-day admin-facing CS an operator runs against the
materialized installation.

**Regenerate this figure** (after editing
``py3/images/airflow-graphviz.pcs``):

::

   cd py3/images
   ./airflow-graphviz.pcs --format=all -i ngProcess all

.. _table-of-contents:

Table of Contents TOC
=====================

-  `Overview <#overview>`__
-  `Package Documentation At
   Github <#package-documentation-at-github>`__
-  `Capability Materialization <#capability-materialization>`__
-  `The 4 systemd Units and DB
   Init <#the-4-systemd-units-and-db-init>`__
-  `Installation <#installation>`__

   -  `Installation With pip <#installation-with-pip>`__
   -  `Installation With pipx <#installation-with-pipx>`__

-  `Usage <#usage>`__

   -  `Day-to-Day Admin:
      ``airflowAdmin.cs`` <#day-to-day-admin-airflowadmincs>`__
   -  `Direct Airflow CLI Cheat Sheet:
      ``quickAirflow.cs`` <#direct-airflow-cli-cheat-sheet-quickairflowcs>`__

-  `Key Files <#key-files>`__
-  `Part of BISOS — ByStar Internet Services Operating
   System <#part-of-bisos--bystar-internet-services-operating-system>`__
-  `Documentation and Blee-Panels <#documentation-and-blee-panels>`__
-  `Support <#support>`__

The 4 systemd Units and DB Init
===============================

Four planted ``*-sysd.pcs`` units live in ``py3/bin/``, all delegating
to the same ``airflow`` CLI executable, each running a different
sub-command:

+-------------+-------------+-------------+-------------+-------------+
| Unit        | Airflow     | ``          | Type        | Ordering    |
|             | role        | ExecStart`` |             |             |
|             |             | sub-command |             |             |
+=============+=============+=============+=============+=============+
| `           | DB          | ``airflow d | `           | ``A         |
| `airflow-db | migration   | b migrate`` | `oneshot``, | fter=networ |
| -sysd.pcs`` |             |             | `           | k.target``; |
|             |             |             | `RemainAfte | runs first  |
|             |             |             | rExit=yes`` |             |
+-------------+-------------+-------------+-------------+-------------+
| ``airflo    | API/Web     | ``airflow a | l           | ``Requ      |
| w-webserver | server      | pi-server - | ong-running | ires=/=Afte |
| -sysd.pcs`` |             | -port ...`` | ``simple``  | r=airflow-d |
|             |             |             |             | b.service`` |
+-------------+-------------+-------------+-------------+-------------+
| ``airflo    | Scheduler   | ``airflow   | l           | ``Requ      |
| w-scheduler |             | scheduler`` | ong-running | ires=/=Afte |
| -sysd.pcs`` |             |             | ``simple``  | r=airflow-d |
|             |             |             |             | b.service`` |
+-------------+-------------+-------------+-------------+-------------+
| ``airflo    | Triggerer   | ``airflow   | l           | ``Requ      |
| w-triggerer | (deferrable | triggerer`` | ong-running | ires=/=Afte |
| -sysd.pcs`` | tasks)      |             | ``simple``  | r=airflow-d |
|             |             |             |             | b.service`` |
+-------------+-------------+-------------+-------------+-------------+

``airflow-db-sysd.pcs`` is a ``oneshot`` unit with
``RemainAfterExit=yes``: it runs ``airflow db migrate`` once to bring
the metadata database schema up to date, then reports itself "active"
without staying resident. The three long-running units each declare
``Requires=/=After=airflow-db.service``, so systemd guarantees the
migration has been attempted before any of the three service processes
starts.

All four units, together with package installation, are declared by
``py3/bin/airflow-cbs.pcs`` and materialized at this host via
``py3/bin/cbmProc-airflow.spcs``.

Installation
============

| The sources for the bisos.airflow pip package are maintained at:
| https://github.com/bisos-pip/airflow

| The bisos.airflow pip package is available at PYPI as
| https://pypi.org/project/bisos.airflow

You can install bisos.airflow with pip or pipx.

Installation With pip
---------------------

If you need access to bisos.airflow as a python module, install it with
pip:

.. code:: bash

   pip install bisos.airflow

Installation With pipx
----------------------

If you only need access to bisos.airflow on the command line, install it
with pipx:

.. code:: bash

   pipx install bisos.airflow

The following commands are made available:

-  ``airflowAdmin.cs`` — day-to-day admin CS for this host's
   ``airflow.here`` installation.
-  ``quickAirflow.cs`` — direct-command cheat sheet for the ``airflow``
   CLI and its ``systemd`` units.
-  ``airflow-cbs.pcs`` — Capability Bundle Specification: declares sbom
   + the 4 sysd units + assemble.
-  ``cbmProc-airflow.spcs`` — planted CBM pointer that materializes the
   CBS at this host.
-  ``airflow-sbom.pcs`` — package installation via
   `bisos.sbom <https://github.com/bisos-pip/sbom>`__.
-  ``airflow-db-sysd.pcs``, ``airflow-webserver-sysd.pcs``,
   ``airflow-scheduler-sysd.pcs``, ``airflow-triggerer-sysd.pcs`` — the
   4 systemd units.
-  ``airflow-assemble.cs`` — assembly/glue step.
-  ``airflow-here-dns.pcs`` — registers the ``.here`` fake-domain DNS
   entry (``airflow.here``).

Usage
=====

Day-to-Day Admin: ``airflowAdmin.cs``
-------------------------------------

Run with no arguments (or ``-i examples``) to see the full menu. Key
sub-commands:

.. code:: bash

   airflowAdmin.cs -i hostInfo       # fqdn, port, AIRFLOW_HOME, DAG dir, log dir
   airflowAdmin.cs -i servicesInfo   # links for operating the 4 systemd units
   airflowAdmin.cs -i usersInfo      # list/create users; default admin/password
   airflowAdmin.cs -i fullUpdate     # all three together

Direct Airflow CLI Cheat Sheet: ``quickAirflow.cs``
---------------------------------------------------

For direct ``airflow`` CLI / ``systemctl`` / ``journalctl`` invocations
(not routed through ``airflowAdmin.cs``), run:

.. code:: bash

   quickAirflow.cs

Key Files
=========

An overview of the relevant files of the bisos.airflow package
(starting-point; to be expanded as the package develops):

-  ``py3/bin/airflowAdmin.cs`` — day-to-day admin CS (hostInfo,
   servicesInfo, usersInfo, fullUpdate).
-  ``py3/bin/quickAirflow.cs`` — direct-command cheat sheet for the
   ``airflow`` CLI and systemd units.
-  ``py3/bin/airflow-cbs.pcs`` — CBS declaring the bundle (sbom + 4 sysd
   units + assemble).
-  ``py3/bin/cbmProc-airflow.spcs`` — planted CBM pointer leaf that
   materializes the CBS.
-  ``py3/bin/airflow-sbom.pcs`` — package installation via
   `bisos.sbom <https://github.com/bisos-pip/sbom>`__.
-  ``py3/bin/airflow-db-sysd.pcs`` — oneshot DB migration unit.
-  ``py3/bin/airflow-webserver-sysd.pcs``,
   ``airflow-scheduler-sysd.pcs``, ``airflow-triggerer-sysd.pcs`` — the
   three long-running units.
-  ``py3/bin/airflow-assemble.cs`` — assembly/glue step.
-  ``py3/bin/airflow-here-dns.pcs`` — ``.here`` fake-domain DNS
   registration for ``airflow.here``.
-  ``py3/images/airflow-graphviz.pcs`` — source for the Capability
   Materialization figure.
-  ``py3/tests/verify.sh`` — smoke test for ``airflowAdmin.cs`` and
   ``quickAirflow.cs``.
-  ``py3/setup.py``, ``py3/pypiProc.sh`` — PyPI packaging (setup.py is
   dblock-driven; do not hand-edit).

Part of BISOS — ByStar Internet Services Operating System
=========================================================

Layered on top of Debian, **BISOS** (By\* Internet Services Operating
System) is a unified and universal framework for developing both
internet services and software-service continuums that use internet
services. See `Bootstrapping ByStar, BISOS and
Blee <https://github.com/bxGenesis/start>`__ for information about
getting started with BISOS.

**BISOS** is a foundation for **The Libre-Halaal ByStar Digital
Ecosystem** which is described as a cure for losses of autonomy and
privacy in a book titled: `Nature of
Polyexistentials <https://github.com/bxplpc/120033>`__

*bisos.airflow* is part of BISOS. It is a standalone package that can be
used independently of the full BISOS environment.

Documentation and Blee-Panels
=============================

bisos.airflow is part of the ByStar Digital Ecosystem
http://www.by-star.net.

This module's primary documentation is in the form of Blee-Panels.
Blee-Panels are in the ``./panels`` directory. From within Blee and
BISOS these panels are accessible under the Blee "Panels" menu.

See
`file:./panels/bisos.airflow/_nodeBase_/fullUsagePanel-en.org <./panels/bisos.airflow/_nodeBase_/fullUsagePanel-en.org>`__
for a starting point.

*bisos.airflow* is best developed with
`Blee <https://github.com/bx-blee>`__, the *By\* BISOS Libre-Halaal
Emacs Environment* — a layer on top of Emacs and BISOS which creates a
comprehensive integrated usage and development environment.

Support
=======

| For support, criticism, comments and questions; please contact the
  author/maintainer
| `Mohsen Banan <http://mohsen.1.banan.byname.net>`__ at:
  http://mohsen.1.banan.byname.net/contact
