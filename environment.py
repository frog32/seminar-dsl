class SysGlobal(object):
    readonly = ('locals', 'globals')

    def __init__(self, env):
        self.env = env

    def __getitem__(self, value):
        if value == 'locals':
            return self.env.stack[-1]
        if value == 'globals':
            return self.env.stack
        raise IndexError('nicht vorhanden')


class StdLen(object):
    def __init__(self, env):
        self.env = env

    def __call__(self, target):
        target.set_namespace(self.env)
        return len(target)


class Environment(object):
    def __init__(self, stack=None):
        if stack is None:
            self.stack = [{}]
        else:
            self.stack = stack
        self.globals = {}
        self.backlog = []
        self.out_handlers = []

        # std globals
        self.register_global('sys', SysGlobal(self))
        self.register_global('len', StdLen(self))

    def stdout(self, text):
        for o in self.out_handlers:
            o('std', text)

    def stderr(self, text):
        for o in self.out_handlers:
            o('error', text)

    def register_outhandler(self, function):
        self.out_handlers.append(function)

    def register_global(self, key, obj):
        self.globals[key] = obj

    def evaluate_statement_list(self, statement_list):
        try:
            statement_list.evaluate(self)
        except Exception as e:
            self.stderr(str(e))

    def push_stacklevel(self):
        self.stack.append({})

    def pop_stacklevel(self):
        self.stack.pop()

    def get_highest_level(self, key):
        for level in range(len(self.stack) - 1, -1, -1):
            if key in self.stack[level]:
                return level
        if key in self.globals:
            return -1  # global
        return None

    def __repr__(self):
        return repr(self.stack)

    def __getitem__(self, key):
        level = self.get_highest_level(key)
        if level is None:
            raise KeyError('key %s is not defined' % key)
        if level == -1:  # global
            return self.globals[key]
        return self.stack[level][key]

    def __setitem__(self, key, value):
        level = self.get_highest_level(key)
        if level is None:
            level = len(self.stack) - 1
        if level == -1:  # global
            # self.globals[key][1](value)
            return
        self.stack[level][key] = value

    def set_local_key(self, key, value):
        level = len(self.stack) - 1
        self.stack[level][key] = value

    def __cmp__(self, other):
        return cmp(self.stack, other.stack)
