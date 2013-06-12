import operator


class StatementList(object):
    def __init__(self, statement):
        self.list = [statement]

    def __repr__(self):
        return '\n'.join(repr(l) for l in self.list)

    def append(self, statement):
        self.list.append(statement)

    def evaluate(self, namespace):
        for statement in self.list:
            statement.evaluate(namespace)


class Statement(object):
    pass


class Assignment(Statement):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def evaluate(self, namespace):
        self.left.set_namespace(namespace).value = self.right.set_namespace(namespace).value

    def __repr__(self):
        return "<Assignment %s = %s>" % (self.left, self.right)


class Nop(Statement):
    def evaluate(self, namespace):
        pass


class PrintStatement(Statement):
    def __init__(self, expr):
        self.expr = expr

    def evaluate(self, namespace):
        namespace.stdout(self.expr.set_namespace(namespace).value)


class Expression(object):
    def __init__(self, sub_expr):
        self.sub_expr = sub_expr

    def __repr__(self):
        return repr(self.sub_expr)

    @property
    def value(self):
        if isinstance(self.sub_expr, Variable):
            return self.sub_expr.set_namespace(self.namespace).value
        elif type(self.sub_expr) in (int, unicode, str, list):
            return self.sub_expr
        else:
            raise TypeError('cant get value of %s' % type(self.sub_expr))

    def set_namespace(self, namespace):
        self.namespace = namespace
        return self


class TwoValueOperation(Expression):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return '%s %s %s' % (self.left, self.operation, self.right)

    @property
    def value(self):
        return self.operation(self.left.set_namespace(self.namespace).value, self.right.set_namespace(self.namespace).value)


class Addition(TwoValueOperation):
    operation = operator.add


class Substraction(TwoValueOperation):
    operation = operator.sub


class Multiplication(TwoValueOperation):
    operation = operator.mul


class Division(TwoValueOperation):
    operation = operator.div


class Variable(Expression):
    def __init__(self, name):
        self.name = name
        self.subscriptions = []

    def __repr__(self):
        return "<Variable %s>" % self.name

    def add_subscription(self, sub):
        self.subscriptions.append(sub)

    def sub_to_index(self, sub):
        if isinstance(sub, Expression):
            return sub.set_namespace(self.namespace).value
        return sub

    def __len__(self):
        if not self.subscriptions:
            return len(self.namespace[self.name])
        var = self.namespace[self.name]
        for sub in self.subscriptions:
            var = var[self.sub_to_index(sub)]
        return len(var)

    @property
    def value(self):
        if not self.subscriptions:
            return self.namespace[self.name]
        var = self.namespace[self.name]
        for sub in self.subscriptions:
            var = var[self.sub_to_index(sub)]
        return var

    @value.setter
    def value(self, value):
        if not self.subscriptions:
            self.namespace[self.name] = value
            return
        var = self.namespace[self.name]
        for sub in self.subscriptions[:-1]:
            var = var[self.sub_to_index(sub)]
        var[self.sub_to_index(self.subscriptions[-1])] = value

    @value.deleter
    def value(self):
        del self.namespace[self.name]


class Forloop(object):
    def __init__(self, varname, iterable, block):
        self.varname = varname
        self.iterable = iterable
        self.block = block

    def evaluate(self, namespace):
        for var in self.iterable.set_namespace(namespace).value:
            namespace.push_stacklevel()
            namespace.set_local_key(self.varname, var)
            self.block.evaluate(namespace)
            namespace.pop_stacklevel()


class If(object):
    def __init__(self, condition, block):
        self.condition = condition
        self.block = block

    def __repr__(self):
        return "<if %s [%s]>" % (self.condition, self.block)

    def evaluate(self, namespace):
        if self.condition.set_namespace(namespace).value:
            self.block.evaluate(namespace)


class Call(Expression):
    def __init__(self, function, *args):
        self.function = function
        self.args = args

    @property
    def value(self):
        return self.function.set_namespace(self.namespace).value(*self.args)
