 .. Licensed to the Apache Software Foundation (ASF) under one
    or more contributor license agreements.  See the NOTICE file
    distributed with this work for additional information
    regarding copyright ownership.  The ASF licenses this file
    to you under the Apache License, Version 2.0 (the
    "License"); you may not use this file except in compliance
    with the License.  You may obtain a copy of the License at
 ..   http://www.apache.org/licenses/LICENSE-2.0
 .. Unless required by applicable law or agreed to in writing,
    software distributed under the License is distributed on an
    "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
    KIND, either express or implied.  See the License for the
    specific language governing permissions and limitations
    under the License.

Platform Setup
==============

Platform is a configuration-driven selection of particular *providers* implementing four abstract concepts:

* :doc:`runner/index`
* :doc:`registry/index`
* :doc:`feed`
* :doc:`sink`

ForML uses internal *bank* of available provider implementations of the different possible types. Provider instances are
registered in this bank using one of two possible *references*:

* provider's *fully qualified class name* - for example the ``forml.lib.runner.dask:Runner``
* for convenience, each provider can also optionally have an *alias* defined by its author - ie ``dask``

.. note:: For any provider implementation to be placed into the ForML provider bank, it needs to get imported somehow.
          When the bank is queried for any provider instance using its reference, it either is matched and returned or
          ForML attempts to import it. If it is queried using the fully qualified class name, it is clear where to
          import it from (assuming the module is on ``sys.path``). If it is however referenced by the alias, ForML only
          considers providers from the :doc:`main library <lib>` shipped with ForML. This means external providers
          cannot be referenced using their aliases as ForML has no chance knowing where to import them from.

Configuration File
------------------
ForML platform uses the `TOML <https://github.com/toml-lang/toml>`_ configuration file format. The system will try to
locate and merge the ``config.toml`` in the following places (in order of parsing/merging - later overrides previous):

+-----------------+--------------------------------------------------------------------+
| Location        | Meaning                                                            |
+=================+====================================================================+
| ``/etc/forml``  | **System** wide global configuration                               |
+-----------------+--------------------------------------------------------------------+
| ``~/.forml``    | **User** homedir configuration (unless ``$FORML_HOME`` is set)     |
+-----------------+--------------------------------------------------------------------+
| ``$FORML_HOME`` | Alternative **user** configuration to the *homedir* configuration  |
+-----------------+--------------------------------------------------------------------+

.. note:: Both the *system* and the *user* config locations are also appended to the runtime ``sys.path`` so any python
          modules stored into the config directories are potentially importable. This can be useful for the custom
          `Feed Providers`_ implementations.

Example ForML platform configuration::

    logcfg = "logging.ini"

    [RUNNER]
    default = "compute"

    [RUNNER.compute]
    provider = "dask"
    scheduler = "multiprocessing"

    [RUNNER.visual]
    provider = "graphviz"
    format = "png"


    [REGISTRY]
    default = "homedir"

    [REGISTRY.virtual]
    provider = "virtual"

    [REGISTRY.homedir]
    provider = "filesystem"
    #path = ~/.forml/registry


    [SINK]
    default = "stdout"

    [SINK.stdout]
    provider = "stdout"


The file can contain configurations of multiple different provider instances labelled with custom alias - here for
example the ``[RUNNER.compute]`` and ``[RUNNER.visual]`` are two configurations of different runners. The actual runner
instance used at runtime out of these two configured is either user-selected (ie the ``-R`` `CLI`_ argument) or
taken from the ``default`` reference from the main ``[RUNNER]`` config section.

All of the provider configurations must contain the option ``provider`` referring to the provider key used by the
internal ForML bank mentioned above. Any other options specified within the provider section are considered to be
arbitrary configuration arguments specific to given provider implementation.

Feed Providers
--------------

Among the different *provider* types, :doc:`Feeds <feed>` are unique as each instance usually needs to be special
implementation specific to the given platform. Part of the feed functionality is to resolve the :ref:`catalogized
schemas <io-catalogized-schemas>` to the physical datasets known to the platform. This might not be always possible via
configuration and the whole feed needs to be implemented as code. For this purpose the *system* and *user* configuration
directories are also potentially searched by the provider importer so that the custom feeds can be placed there.

For example the following feed implementation stored under ``~/.forml/tutorial.py`` can be referenced from the config
file simply as ``tutorial:Feed``::

    from forml.io import feed
    from forml.lib.reader import sqlite
    from forml.lib.schema.kaggle import titanic


    class Feed(feed.Provider):
        class Reader(sqlite.Reader):
        @property
        def sources(self):
            return {titanic.Passenger: 'passenger'}


Logging
-------

Python logger is used throughout the framework to emit various logging messages. The logging config can be customized
using a config file specified in the top-level ``logcfg`` option in the main `configuration file`_.

.. _platform-cli:

CLI
---

The production :doc:`lifecycle <lifecycle>` management can be fully operated from command-line using the following
syntax:

.. code-block:: none

    usage: forml [-h] [-C CONFIG] [-P REGISTRY] [-R RUNNER] [-E ENGINE]
                 {init,list,tune,train,apply} ...

    Lifecycle Management for Datascience Projects

    positional arguments:
      {init,list,tune,train,apply}
                            program subcommands (-h for individual description)
        init                create skeleton for a new project
        list                show the content of the selected registry
        tune                tune the given project lineage producing new
                            generation
        train               train new generation of given project lineage
        apply               apply given generation of given project lineage

    optional arguments:
      -h, --help            show this help message and exit
      -C CONFIG, --config CONFIG
                            additional config file
      -P REGISTRY, --registry REGISTRY
                            persistent registry reference
      -R RUNNER, --runner RUNNER
                            runtime runner reference
      -E ENGINE, --engine ENGINE
                            IO engine reference
