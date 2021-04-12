class A:
    def __init__(self):
        print("Init x")
        self._x = 0

    @property
    def x(self):
        print("Get x")
        return self._x

class B(A):
    @A.x.setter
    def x(self, value):
        print("Set x")
        self._x = value


if __name__ == '__main__':
    a = A()
    print(a.x)
    b = B()
    print(b.x)
    b.x = 2
    a.x = 5
