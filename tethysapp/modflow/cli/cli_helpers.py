import os


def print_error(statement):
    print('{}{}{}'.format('\033[91m', statement, '\033[0m'))


def print_success(statement):
    print('{}{}{}'.format('\033[92m', statement, '\033[0m'))


def print_warning(statement):
    print('{}{}{}'.format('\033[93m', statement, '\033[0m'))


def print_info(statement):
    print('{}{}{}'.format('\033[94m', statement, '\033[0m'))


def print_header(statement):
    print('{}{}{}'.format('\033[95m', statement, '\033[0m'))


class PGPassManager(object):
    def __init__(self):
        self.path = self.get_path()
        self.content = self.get_content()

    @staticmethod
    def get_path():
        this_usr_dir = os.path.expanduser('~/')
        return os.path.join(this_usr_dir, '.pgpass')

    def get_content(self):
        pg_pass_content = ''

        if os.path.exists(self.path):
            with open(self.path, 'r') as f:
                pg_pass_content = f.read()

        return pg_pass_content

    def restore_content(self):
        with open(self.path, 'w+') as f:
            f.write(self.content)

    def add_entry_if_not_exists(self, host, port, db_name, username, password):
        entry = '{}:{}:{}:{}:{}'.format(host, port, db_name, username, password)
        if entry not in self.content:
            with open(self.path, 'a') as f:
                f.write(entry)
                f.write('\n')
