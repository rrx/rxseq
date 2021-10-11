import collections
import functools
import importlib
import math
import os
import threading


def nested_dict():
    return collections.defaultdict(nested_dict)


class DynamicNamespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __getattr__(self, key):
        return self.__dict__.get(key)

    def __setattr__(self, key, value):
        if not key.startswith('_'):
            self.__dict__[key] = value

    def get_or_create(self, key, default=None):
        initialize = key not in self.__dict__
        value = self.__dict__.get(key, default)
        if initialize:
            self.__dict__[key] = value
        return value

    def update(self, args):
        self.__dict__.update(args)

    def __repr__(self):
        return "%s" % self.__dict__


class State(DynamicNamespace):
    pass


def initialize_default(state, key, default):
    if getattr(state, key) is None:
        setattr(state, key, default)
    return getattr(state, key)


def get_latest_version_of_function(f):
    name = f.__name__
    module = importlib.import_module(f.__module__)
    f_before = module.__dict__[name]
    importlib.reload(module)
    f_after = module.__dict__[name]
    # if f_after != f_before:
    #     print("update on", name, f_before, f_after)
    return f_after


def call_live(f, *args, **kwargs):
    return get_latest_version_of_function(f)(*args, **kwargs)


class LiveCodeThread(threading.Thread):
    def __init__(self, step, initialize=None, reload=None, state=None, **kwargs):
        self._step = step
        self._reload = reload
        self._initialize = initialize
        self._changes = nested_dict()

        if state is None:
            state = DynamicNamespace(**kwargs)

        self.state = state

        threading.Thread.__init__(self)
        # return
        #
        # # TODO: if the module is the main module, we aren't able to handle that yet
        # functions = list(filter(lambda x: x and x.__module__ != '__main__', [step, initialize, reload]))
        #
        # def function_to_module(function):
        #     return importlib.import_module(function.__module__)
        #
        # def function_to_dict(function):
        #     module = function_to_module(function)
        #     return module.__file__, {'function': function, 'module': module, 'filename': module.__file__, 'mtime': os.stat(module.__file__).st_mtime_ns}
        #
        # self._changes = dict(map(function_to_dict, functions))

    def reload_if_changed(self, spec):
        filename = spec['filename']
        module = spec['module']

        try:
            # last_change = self._changes[filename]
            mtime = os.stat(filename).st_mtime_ns
            if mtime != spec['mtime']:
                module2 = importlib.import_module(spec['function'].__module__)
                importlib.reload(module)
                spec['mtime'] = mtime
                return spec

        except:
            import traceback
            traceback.print_exc()

    def reload(self):
        specs_to_reload = [self.reload_if_changed(spec) for spec in self._changes.values()]
        if any(specs_to_reload):
            if self._reload is not None:
                self._reload(self.state)

        for spec in specs_to_reload:
            if spec:
                print("reload", spec['module'].__name__)

    def update_latest(self, f):
        name = f.__name__
        updated_function = get_latest_version_of_function(f)
        self.__dict__[name] = updated_function
        return updated_function

    def run(self):
        if self._initialize is not None:
            self.update_latest(self._initialize)(self.state)

        while True:
            self.update_latest(self._step)(self.state)


def start_live_thread(step, initialize=None, state=None, **kwargs):
    t = LiveCodeThread(step, initialize=initialize, state=state, **kwargs)
    t.start()


class SimpleThread(threading.Thread):
    def __init__(self, f, *args, **kwargs):
        self.f = f
        self.args = args
        self.kwargs = kwargs
        threading.Thread.__init__(self)

    def run(self):
        try:
            self.f(*self.args, **self.kwargs)
        except:
            import traceback
            traceback.print_exc()


def start_in_thread(f, *args, **kwargs):
    t = SimpleThread(f, *args, **kwargs)
    t.start()


def compose(*functions):
    return functools.reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)


def map_value(value, input_mapping=None, output_mapping=None, symmetric=False, exponent=1):
    if input_mapping is None:
        input_mapping = (0,1)
    if output_mapping is None:
        output_mapping = (0,1)

    input_width = input_mapping[1] - input_mapping[0]
    output_width = output_mapping[1] - output_mapping[0]

    value = (value - input_mapping[0]) / input_width
    if exponent != 1:
        if symmetric and value >= 0.5:
            value = (pow((value - 0.5) * 2, exponent) / 2) + 0.5
        elif symmetric and value < 0.5:
            value = (1 - pow(1 - (value * 2), exponent)) / 2
        else:
            value = pow(value, exponent)
    value = (value * output_width) + output_mapping[0]
    assert not math.isnan(value)
    assert not math.isinf(value)
    return value


def value_transformer(**kwargs):
    return lambda value: map_value(value, **kwargs)


def encoder(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError(repr(obj) + " is not JSON serializable")

