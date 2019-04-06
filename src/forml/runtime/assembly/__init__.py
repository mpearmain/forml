import abc
import collections
import logging
import time
import typing

from forml import project as prjmod, etl
from forml.flow.graph import view, node as grnode
from forml.runtime import persistent
from forml.runtime.assembly import instruction as instmod, symbol as symbmod

LOGGER = logging.getLogger(__name__)


class Instruction(metaclass=abc.ABCMeta):
    """Callable part of an assembly symbol that's responsible for implementing the processing activity.
    """
    @abc.abstractmethod
    def execute(self, *args: typing.Any) -> typing.Any:
        """Instruction functionality.

        Args:
            *args: Sequence of input arguments.

        Returns: Instruction result.
        """

    def __str__(self):
        return f'{self.__class__.__name__}[{id(self)}]'

    def __call__(self, *args: typing.Any) -> typing.Any:
        LOGGER.debug('%s invoked (%d args)', self, len(args))
        start = time.time()
        result = self.execute(*args)
        LOGGER.debug('%s completed (%.2fms)', self, (time.time() - start) * 1000)
        return result


class Symbol(collections.namedtuple('Symbol', 'instruction, arguments')):
    """Main entity of the assembled code.
    """
    def __new__(cls, instruction: Instruction, arguments: typing.Optional[typing.Sequence[Instruction]] = None):
        if arguments is None:
            arguments = []
        assert all(arguments), 'All arguments required'
        return super().__new__(cls, instruction, tuple(arguments))

    def __str__(self):
        return f'{self.instruction}{self.arguments}'


class Visitor(view.Visitor, metaclass=abc.ABCMeta):
    """Symbol visitor base class.
    """
    def __init__(self) -> None:
        self._table: symbmod.Table = symbmod.Table()

    def visit_node(self, node: grnode.Worker) -> None:
        """Expanding node into a (set of) symbols.

        Args:
            node: Node to be visited.
        """
        self._table.add(node)

    def visit_path(self, path: 'view.Path') -> None:
        """Path visitor hook.

        Args:
            path: Path to be visited.
        """
        for symbol in self._table:
            self.visit_symbol(symbol)

    @abc.abstractmethod
    def visit_symbol(self, symbol: Symbol) -> None:
        """Actual symbol visit logic - to be implemented by particular interpreters.

        Args:
            symbol: Visited symbol.
        """


class Code:
    """Linked assembly code
    """
    def __init__(self, path: view.Path):
        self._path: view.Path = path

    def accept(self, visitor: Visitor) -> None:
        """Visit the code symbols.
        """
        self._path.accept(visitor)


class Linker:
    """Linker is doing the hard work of assembling the low-level task graph based on the selected mode combining with
    particular ETL engine and possibly any persistence steps.
    """
    def __init__(self, engine: etl.Engine, project: prjmod.Descriptor, assets: persistent.Assets):
        self._engine: etl.Engine = engine
        self._project: prjmod.Descriptor = project
        self._assets: persistent.Assets = assets

    @classmethod
    def load(cls, engine: etl.Engine, ) -> 'Linker':
        """Create the linker instance based on project loaded from a registry.

        Args:
            engine: ETL engine to use.

        Returns: Linker instance.
        """

    @property
    def training(self) -> Code:
        """Return the training code.

        Returns: Training code.
        """