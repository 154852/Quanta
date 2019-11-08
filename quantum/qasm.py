import re
import quantum as Q
from math import sqrt

class Instruction:
    TYPES = []

    @staticmethod
    def parse(text): pass
    @staticmethod
    def name(): return ""

    def execute(self, env): pass

class AllocateRegister(Instruction):
    def __init__(self, size, dtype, address):
        self.size = size
        self.dtype = dtype
        self.address = address

    def execute(self, env):
        if self.dtype == None: return
        env.overwrite(self.address, self.address + self.size, list(Q.create_register(self.size)) if self.dtype == "Q" else [0 for i in range(self.size)])

    @staticmethod
    def name(): return "alloc"

    @staticmethod
    def parse(text):
        m = re.match(r"^alloc ([0-9]+)((Q|b)\(([0-9]+)\))?$", text)
        if m != None:
            groups = m.groups()
            return AllocateRegister(int(groups[0]), groups[2], int(groups[3]) if groups[3] != None else None)    
Instruction.TYPES.append(AllocateRegister)

class MGate(Instruction):
    def __init__(self, address, output):
        self.address = address
        self.output = output

    @staticmethod
    def name(): return "M"

    def execute(self, env):
        env.memory[self.output] = env.memory[self.address].M(rtype=int)

    @staticmethod
    def parse(text):
        m = re.match(r"^M ([0-9]+)Q,\s*([0-9]+)b$", text)
        if m != None:
            groups = m.groups()
            return MGate(int(groups[0]), int(groups[1]))    
Instruction.TYPES.append(MGate)

class Label(Instruction):
    def __init__(self, name):
        self.name = name

    @staticmethod
    def name(): return "Label"

    def execute(self, env): pass

    @staticmethod
    def parse(text):
        m = re.match(r"^(\.[a-z_A-Z0-9]+):$", text)
        if m != None:
            return Label(m.groups()[0])
Instruction.TYPES.append(Label)

def create_gate_class(method):
    params = method.__code__.co_varnames[1:]

    regex = r"^" + method.__name__ + r" ([0-9]+)Q"
    if len(params) == 1: regex += r",\s*([0-9.]+)b"
    regex += r"$"

    class Gate(Instruction):
        def __init__(self, *args):
            self.args = args

        @staticmethod
        def name(): return method.__name__

        def execute(self, env):
            method(env.memory[self.args[0]], *self.args[1:])

        @staticmethod
        def parse(text):
            m = re.match(regex, text)
            if m != None:
                groups = m.groups()
                return Gate(int(groups[0]), *[float(groups[i + 1]) for i in range(len(params))])

    return Gate

def create_gate_class_multi(method):
    params = method.__code__.co_varnames
    regex = r"^" + method.__name__ + " " + ",".join([r"\s*([0-9]+)Q" for _ in range(len(params))]) + r"$"

    class Gate(Instruction):
        def __init__(self, args):
            self.args = args

        @staticmethod
        def name(): return method.__name__

        def execute(self, env):
            method(*[env.memory[addr] for addr in self.args])

        @staticmethod
        def parse(text):
            m = re.match(regex, text)
            if m != None:
                groups = m.groups()
                return Gate([int(groups[i]) for i in range(len(params))])

    return Gate

for m in [*"XYZH", "SQRTX", "ZX"]:
    method = vars(Q.Qubit)[m]
    Instruction.TYPES.append(create_gate_class(method))

for m in [Q.CNOT, Q.CCNOT]:
    Instruction.TYPES.append(create_gate_class_multi(m))

def create_basic_operation(name, func):
    class Operation(Instruction):
        def __init__(self, a, b):
            self.a, self.b = a, b

        @staticmethod
        def name(): return name

        def execute(self, env):
            func(env, env.read_from_address(self.a), self.b)

        @staticmethod
        def parse(text):
            m = re.match(r"^" + name + r" ([0-9]+b?),\s*([0-9]+)b$", text)
            if m != None:
                groups = m.groups()
                return Operation(groups[0], int(groups[1]))
    
    return Operation

def create_jmp_operation(name, func):
    class Operation(Instruction):
        def __init__(self, l):
            self.label = l

        @staticmethod
        def name(): return name

        def execute(self, env):
            if func(env): env.PC = env.labels[self.label]

        @staticmethod
        def parse(text):
            m = re.match(r"^" + name + r" (\.[a-z_A-Z0-9]+)$", text)
            if m != None:
                groups = m.groups()
                return Operation(groups[0])
    
    return Operation

def add(env, a, b): env.memory[b] += a
Instruction.TYPES.append(create_basic_operation("add", add))
def sub(env, a, b): env.memory[b] -= a
Instruction.TYPES.append(create_basic_operation("sub", sub))
def mul(env, a, b): env.memory[b] *= a
Instruction.TYPES.append(create_basic_operation("mul", mul))
def div(env, a, b): env.memory[b] //= a
Instruction.TYPES.append(create_basic_operation("div", div))
def mov(env, a, b): env.memory[b] = a
Instruction.TYPES.append(create_basic_operation("mov", mov))
def cmp(env, a, b): env.a, env.b = a, env.memory[b]
Instruction.TYPES.append(create_basic_operation("cmp", cmp))
Instruction.TYPES.append(create_jmp_operation("jmp", lambda env: True))
Instruction.TYPES.append(create_jmp_operation("jgt", lambda env: env.a > env.b))
Instruction.TYPES.append(create_jmp_operation("jlt", lambda env: env.a < env.b))
Instruction.TYPES.append(create_jmp_operation("je", lambda env: env.a == env.b))
Instruction.TYPES.append(create_jmp_operation("jne", lambda env: env.a != env.b))
Instruction.TYPES.append(create_jmp_operation("jle", lambda env: env.a <= env.b))
Instruction.TYPES.append(create_jmp_operation("jge", lambda env: env.a >= env.b))

class Environment:
    def __init__(self, mem_size, labels):
        self.memory = [None for _ in range(mem_size)]
        self.PC = 0
        self.labels = labels
        self.a, self.b = None, None

    def next(self): self.PC += 1

    def overwrite(self, start, end, values):
        for i in range(start, end, 1):
            self.memory[i] = values[i - start]

    def count(self, dtype):
        count = 0
        for item in self.memory:
            if dtype == "Q" and isinstance(item, Q.Qubit): count += 1
            elif dtype == "b" and isinstance(item, int): count += 1
            elif dtype == "u" and item is None: count += 1

        return count

    def read_from_address(self, addr):
        if addr.endswith("b"): return self.memory[int(addr[:-1])]
        return int(addr)

    def toJSON(self):
        return [(b if isinstance(b, int) else None) for b in self.memory]

def compile_qasm(string):
    if type(string) == str: lines = re.split(r"\s*\n\s*", string)
    else: lines = string

    instructions = []
    for line in lines:
        line0 = line
        line = line.split("#")[0].strip()
        if len(line) == 0: continue

        found = False
        for instruction_type in Instruction.TYPES:
            i = instruction_type.parse(line)
            if i is not None:
                instructions.append(i)
                found = True
                break

        if not found:
            raise SyntaxError(f"Invalid qasm instruction '{line0}'")

    return instructions

def execute_qasm(instructions):
    mem_size = 0
    labels = {}
    for i,instruction in enumerate(instructions):
        if isinstance(instruction, AllocateRegister) and instruction.dtype == None: mem_size = instruction.size
        elif isinstance(instruction, Label): labels[instruction.name] = i

    env = Environment(mem_size, labels)
    while env.PC < len(instructions):
        instructions[env.PC].execute(env)
        env.next()

    return env