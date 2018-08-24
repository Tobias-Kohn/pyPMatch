#
# (c) 2018, Tobias Kohn
#
# Created: 24.08.2018
# Updated: 24.08.2018
#
# License: Apache 2.0
#

# TODO: Complete the implementation
# TODO: Make sure it follows already existing designs as far as possible

class MultiFunction(object):

    def __init__(self, name: str):
        self.name = name
        self.functions = []
        raise NotImplementedError("'case' decorators not implemented yet!")

    def __call__(self, *args, **kwargs):
        pass

    def invalidate(self):
        pass

    def register(self, pattern: str, function):
        self.functions.append((pattern, function))
        self.invalidate()
