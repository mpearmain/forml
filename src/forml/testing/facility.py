"""
Testing facility.
"""
import logging
import typing
import uuid

from forml import io
from forml.conf import provider as provcfg
from forml.flow.graph import node as nodemod
from forml.flow.graph import view
from forml.flow.pipeline import topology
from forml.io import etl
from forml.io.dsl import parsing
from forml.io.dsl import statement
from forml.io.dsl.schema import series, frame, kind
from forml.io.etl import extract
from forml.runtime import process
from forml.testing import spec

LOGGER = logging.getLogger(__name__)


class DataSet(etl.Schema):
    """Testing schema.

    The actual fields are irrelevant.
    """
    feature: etl.Field = etl.Field(kind.Integer())
    label: etl.Field = etl.Field(kind.Float())


class Feed(io.Feed, key='testing'):
    """Special feed to feed the test cases.
    """
    def __init__(self, scenario: spec.Scenario.Input, **kwargs):
        super().__init__(**kwargs)
        self._scenario: spec.Scenario.Input = scenario

    @classmethod
    def reader(cls, sources: typing.Mapping[frame.Source, parsing.ResultT],
               columns: typing.Mapping[series.Column, parsing.ResultT],
               **kwargs) -> typing.Callable[[statement.Query], typing.Sequence[typing.Sequence[typing.Any]]]:
        def read(query: statement.Query) -> typing.Any:
            """Reader callback.

            Args:
                query: Input query instance.

            Returns: Data.
            """
            return columns[DataSet.label] if DataSet.label in query.columns else columns[DataSet.feature]
        return read

    @classmethod
    def slicer(cls, schema: typing.Sequence['series.Column'],
               columns: typing.Mapping['series.Column', 'parsing.ResultT']) -> typing.Callable[
                   [extract.Columnar, typing.Union[slice, int]], extract.Columnar]:
        return lambda c, s: c[s][0]

    @property
    def columns(self) -> typing.Mapping[series.Column, parsing.ResultT]:
        return {
            DataSet.label: (self._scenario.train, [self._scenario.label]),
            DataSet.feature: self._scenario.apply
        }


class Runner:
    """Test runner is a minimal forml pipeline wrapping the tested operator.
    """
    class Initializer(view.Visitor):
        """Visitor that tries to instantiate each node in attempt to validate it.
        """
        def __init__(self):
            self._gids: typing.Set[uuid.UUID] = set()

        def visit_node(self, node: nodemod.Worker) -> None:
            if isinstance(node, nodemod.Worker) and node.gid not in self._gids:
                self._gids.add(node.gid)
                node.spec()

    def __init__(self, params: spec.Scenario.Params, scenario: spec.Scenario.Input, runner: provcfg.Runner):
        self._params: spec.Scenario.Params = params
        self._source: etl.Source = etl.Source.query(DataSet.select(DataSet.feature), DataSet.label)
        self._feed: io.Feed = Feed(scenario)
        self._runner: provcfg.Runner = runner

    def __call__(self, operator: typing.Type[topology.Operator]) -> process.Runner:
        instance = operator(*self._params.args, **self._params.kwargs)
        initializer = self.Initializer()
        segment = instance.expand()
        segment.apply.accept(initializer)
        segment.train.accept(initializer)
        segment.label.accept(initializer)
        return self._source.bind(instance).launcher(process.Runner[self._runner.name], self._feed,
                                                    **self._runner.kwargs)
