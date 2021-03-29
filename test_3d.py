from gui.primitives import Primitive
from pattern.pattern import ConstantPattern, LinearPattern, BFSOperatorPattern, SinusoidalPattern

def search(input_parameters: [[float]], extrapolations: int) -> [[float]]:
    if len(input_parameters) == 0:
        return []

    primitive_name = "primitive"
    primitive_arity = len(input_parameters[0])
    primitives = [Primitive(primitive_name, primitive_arity, *primitive_parameters) for primitive_parameters in input_parameters]

    output_parameters = [[] for _ in range(extrapolations)]
    possible_patterns = [ConstantPattern, LinearPattern, BFSOperatorPattern, SinusoidalPattern]

    for index in range(primitive_arity):
        for pattern in possible_patterns:
            result = pattern.apply(primitives, index)
            if result is not None:
                for extrapolation in range(extrapolations):
                    output_parameters[extrapolation].append(result.next(primitives, extrapolation + 1))
                break
        else:
            return []

    return output_parameters