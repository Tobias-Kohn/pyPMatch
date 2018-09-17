#
# (c) 2018, Tobias Kohn
#
# Created: 27.08.2018
# Updated: 14.09.2018
#
# License: Apache 2.0
#
# The basic idea of this example follows the book `Programming in Scala` by M. Odersky, L. Spoon, and B. Venners,
# third edition, p. 595ff.
#

class EMail:

    def __unapply__(self):
        if type(self) is str and '@' in self:
            parts = self.split('@')
            if len(parts) == 2 and '.' in parts[1] and len(parts[0]) > 0:
                return tuple(parts)

        return None


class Handle:

    @staticmethod
    def __unapply__(handle):
        if type(handle) is str and len(handle) > 1:
            if handle[0] == '@':
                return (handle[1:],)
        return None


def get_user_name(email):
    match email:
        case EMail(user, _):
            return "e:" + user
        case Handle(user):
            return "h:" + user
        case _:
            return "?:" + email


def main():
    for email in [
        'monty@python.org',
        'john.doe@python.com',
        'user@noserver',
        'Jane Doe',
        '@myhandle',
        '@follow_me'
    ]:
        print(f"Username of '{email}': '{get_user_name(email)}'")
