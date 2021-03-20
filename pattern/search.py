from typing import Sequence

from pylo.engines import MiniKanren
from pylo.language.commons import Atom

class Search:
    def __init__(self):
        self.solver = MiniKanren()

    @staticmethod
    def search(atoms: Sequence[Atom]):
        pass

    def assertz(self, atoms: Sequence[Atom]):
        for atom in atoms:
            self.solver.assertz(atom)

    def query(self, atom: Atom):
        return self.solver.query(atom)