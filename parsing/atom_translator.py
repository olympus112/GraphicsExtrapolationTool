from gui.primitives import Primitive
from pylo.language.commons import Atom, c_pred


class Translator:
    @staticmethod
    def translate(primitives: [Primitive], predicates = None) -> [Atom]:
        atoms = []
        if predicates is None:
            predicates = dict()

        for primitive in primitives:
            predicate = primitive.name, primitive.arity

            if predicate not in predicates:
                predicates[predicate] = c_pred(*predicate)

            atoms.append(predicates[predicate](*primitive.parameters))

        return atoms, predicates