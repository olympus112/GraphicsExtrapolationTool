from typing import Sequence

from pylo.engines.prolog import SWIProlog

from pylo.engines import MiniKanren
from pylo.language.commons import Atom

class Search:
    def __init__(self):
        self.solver = SWIProlog()

    @staticmethod
    def search(atoms: Sequence[Atom]):
        pass

    def assertz(self, atoms: Sequence[Atom]):
        for atom in atoms:
            self.solver.assertz(atom)

    def retract_all(self):
        self.solver.retract_all()

    def query(self, atom: Atom):
        return self.solver.query(atom)