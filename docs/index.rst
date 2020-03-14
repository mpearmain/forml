.. forml documentation master file

ForML Documentation
===================

ForML is a framework for researching, implementing and operating machine learning projects.

Use ForML to formally describe a machine learning problem as a composition of high-level operators.
ForML expands your project into a task dependency graph specific to given life-cycle phase and executes it
using one of its supported runners.

When machine learning projects are described using formal structured expressions, they become more serviceable,
extensible, reproducible, and collaborative.


Concepts
--------

Formalization
    ForML uses a formal *project component structure* and *workflow expression interface* for high-level project
    description.
Lifecycle
    ForML consistently takes care of all stages of typical ML project lifecycle.
Composition
    ForML uses *operators* as abstraction of actions and topologies that can be composed together to generate complex
    flows from simple expressions.
Runtime
    ForML provides several means of executing the project via integration of established 3rd party data processing
    systems.


Not Just Another DAG
--------------------

Despite *DAG* (directed acyclic graph) is at the heart of ForML operations, it stands out amongst the many other task
dependency processing systems due to:

a. Its specialization on machine learning problems that's wired right into the flow topology
b. Concept of high-level operator composition which helps wrapping complex ML techniques into simple reusable units


Content
-------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   examples
   tutorial

.. toctree::
   :maxdepth: 2
   :caption: Essentials

   principles
   project
   lifecycle
   workflow
   runtime

.. toctree::
   :maxdepth: 2
   :caption: Advanced

   interactive
   config
   operator
   testing

.. toctree::
   :maxdepth: 2
   :caption: Stdlib

.. toctree::
   :maxdepth: 2
   :caption: Runner

   dask
   graphviz

.. toctree::
   :maxdepth: 2
   :caption: Registry

   filesystem