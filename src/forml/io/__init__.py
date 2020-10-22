# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
ETL layer.
"""
import abc
import functools
import typing

from forml import provider as provmod
from forml.conf import provider as provcfg
from forml.flow import task, pipeline
from forml.flow.pipeline import topology
from forml.io import etl as etlmod, payload
from forml.io.dsl import parser
from forml.io.dsl.schema import series, frame, kind as kindmod
from forml.io.feed import extract
from forml.io.sink import publish


class Feed(provmod.Interface, typing.Generic[parser.Source, parser.Column],
           default=provcfg.Feed.default[-1], path=provcfg.Feed.path):
    """Feed is the implementation of a specific datasource provider.
    """
    class Reader(extract.Reader[parser.Source, parser.Column, payload.Native], metaclass=abc.ABCMeta):
        """Abstract reader of the feed.
        """

    def __init__(self, **readerkw):
        self._readerkw: typing.Dict[str, typing.Any] = readerkw

    def load(self, source: 'etlmod.Source', lower: typing.Optional['kindmod.Native'] = None,
             upper: typing.Optional['kindmod.Native'] = None) -> pipeline.Segment:
        """Provide a pipeline composable segment implementing the etl actions.

        Args:
            source: Independent datasource descriptor.
            lower: Optional ordinal lower bound.
            upper: Optional ordinal upper bound.

        Returns: Pipeline segment.
        """
        def formatter(provider: typing.Callable[..., payload.Columnar]) -> typing.Callable[..., typing.Any]:
            """Creating a closure around the provider with the custom formatting to be applied on the provider output.

            Args:
                provider: Original provider whose output is to be formatted.

            Returns: Wrapper that applies formatting upon calling the provider.
            """
            @functools.wraps(provider)
            def wrapper(*args, **kwargs) -> typing.Any:
                """Wrapped provider with custom formatting.

                Args:
                    *args: Original args.
                    **kwargs: Original kwargs.

                Returns: Formatted data.
                """
                return self.format(provider(*args, **kwargs))
            return wrapper

        def actor(handler: typing.Callable[[...], typing.Any], spec: frame.Query) -> task.Spec:
            """Helper for creating the reader actor spec for given query.

            Args:
                handler: Reading handler.
                spec: Data loading statement.

            Returns: Reader actor spec.
            """
            return extract.Reader.Actor.spec(handler, extract.Statement.prepare(
                spec, source.extract.ordinal, lower, upper))

        reader = self.reader(self.sources, self.columns, **self._readerkw)
        query: frame.Query = source.extract.train
        label: typing.Optional[task.Spec] = None
        if source.extract.label:  # trainset/label formatting is applied only after label extraction
            query = query.select(*(*source.extract.train.columns, *source.extract.label))
            label = extract.Slicer.Actor.spec(formatter(self.slicer(query.columns, self.columns)),
                                              source.extract.train.columns, source.extract.label)
        else:  # testset formatting is applied straight away
            reader = formatter(reader)
        train = actor(reader, query)
        apply = actor(formatter(self.reader(self.sources, self.columns, **self._readerkw)), source.extract.apply)
        loader: topology.Composable = extract.Operator(apply, train, label)
        if source.transform:
            loader >>= source.transform
        return loader.expand()

    @classmethod
    def reader(cls, sources: typing.Mapping[frame.Source, parser.Source],
               columns: typing.Mapping[series.Column, parser.Column],
               **kwargs: typing.Any) -> typing.Callable[[frame.Query], payload.Columnar]:
        """Return the reader instance of this feed (any callable, presumably extract.Reader).

        Args:
            sources: Source mappings to be used by the reader.
            columns: Column mappings to be used by the reader.
            kwargs: Optional reader keyword arguments.

        Returns: Reader instance.
        """
        return cls.Reader(sources, columns, **kwargs)  # pylint: disable=abstract-class-instantiated

    @classmethod
    def slicer(cls, schema: typing.Sequence[series.Column],
               columns: typing.Mapping[series.Column, parser.Column]) -> typing.Callable[
                   [payload.Columnar, typing.Union[slice, int]], payload.Columnar]:
        """Return the slicer instance of this feed, that is able to split the loaded dataset column-wise.

        This default slicer is plain positional sequence slicer.

        Args:
            schema: List of expected columns to be sliced from.
            columns: Column mappings to be used by the selector.

        Returns: Slicer instance.
        """
        return extract.Slicer(schema, columns)

    @classmethod
    def format(cls, data: payload.Columnar) -> typing.Any:
        """Optional post-formatting to be applied upon obtaining the columnar data from the raw reader.

        Args:
            data: Input Columnar data to be formatted.

        Returns: Formatted data.
        """
        return data

    @property
    def sources(self) -> typing.Mapping[frame.Source, parser.Source]:
        """The explicit sources mapping implemented by this feed to be used by the query parser.

        Returns: Sources mapping.
        """
        return {}

    @property
    def columns(self) -> typing.Mapping[series.Column, parser.Column]:
        """The explicit columns mapping implemented by this feed to be used by the query parser.

        Returns: Columns mapping.
        """
        return {}


class Sink(provmod.Interface, default=provcfg.Sink.default, path=provcfg.Sink.path):
    """Sink is an implementation of a specific data consumer.
    """
    class Writer(publish.Writer, metaclass=abc.ABCMeta):
        """Abstract sink writer.
        """

    def __init__(self, **writerkw):
        self._writerkw: typing.Dict[str, typing.Any] = writerkw

    def publish(self) -> pipeline.Segment:
        """Provide a pipeline composable segment implementing the publish action.

        Returns: Pipeline segment.
        """
        publisher: topology.Composable = publish.Operator(publish.Writer.Actor.spec(self.writer(**self._writerkw)))
        return publisher.expand()

    @classmethod
    def writer(cls, **kwargs: typing.Any) -> typing.Callable[[payload.Columnar], None]:
        """Return the reader instance of this feed (any callable, presumably extract.Reader).

        Args:
            kwargs: Optional writer keyword arguments.

        Returns: Writer instance.
        """
        return cls.Writer(**kwargs)  # pylint: disable=abstract-class-instantiated
