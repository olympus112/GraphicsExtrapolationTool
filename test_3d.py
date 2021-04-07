from pattern.pattern import *


def search(input_parameters: [[float]], extrapolations: int) -> [[float]]:
    if len(input_parameters) == 0:
        return []

    primitive_arity = len(input_parameters[0])

    output_parameters = [[] for _ in range(extrapolations)]
    possible_patterns = [ConstantPattern, LinearPattern, PeriodicPattern, BFSOperatorPattern, SinusoidalPattern]

    for index in range(primitive_arity):
        parameters = [input_parameter[index] for input_parameter in input_parameters]
        for pattern in possible_patterns:
            flags = ParameterFlags(parameters)
            result = pattern.apply(parameters, index, flags)
            if result is not None:
                for extrapolation in range(extrapolations):
                    new_parameter = result.next(parameters, extrapolation + 1)
                    print(type(new_parameter))
                    output_parameters[extrapolation].append(new_parameter*1.0)
                break
        else:
            return []
    print(output_parameters)

    return output_parameters

# if __name__ == '__main__':
#     print(search([[2.0, 3.0, 0.0, 2.0], [3.0, 3.0, 0.0, 2.0], [0.07699999981559813, 1.0859999998938292, 0.0829999998677522, 2.0]], 4))