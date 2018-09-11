#
# (c) 2018, Tobias Kohn
#
# Created: 11.09.2018
# Updated: 11.09.2018
#
# License: Apache 2.0
#

def get_user_name(arg):
    match arg:
        case user + '@' + _ if user != '':
            return user
        case '@' + user:
            return user
        case _:
            return 'unknown user of ' + arg


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
