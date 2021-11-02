# ==============================================================
#       HIGH-LEVEL TOOL TO MAKE INTERACTIVE CONSOLE APPS
#               WITH VARIABLES & FUNCTIONS
# ==============================================================

import re
class ConsoleApp:
    '''Each instance of this class is a textual input parser, which makes it easy to interpret variable queries, variable setting commands,
    and function calls. When iterated over (or when .input() is called), it requests input from stdin (with a custom prompt), and returns 
    the parsed information, an action, rname, data tuple. 
    'action' tells what type of action did the user make: 'get_var' for a variable query, 'set_var' for a variable setting command, 'func' for
        a function call, 'fail_func' for an improperly formatted function call, 'fail_var' for an improperly formatted command regarding a
        variable, and 'nonsense' if the input could not be interpreted
    'rname' is the name of the variable/command that 'action' refers to
    'data' is additional data: None if not applicable, the input string if 'fail_...' occured, the extracted string representation of the
        variable on 'set_var', and the inputs of the function in case of 'func' in a dictionary
    For more information on these, see ConsoleApp.parse()'s docstring.
    The class uses regexes heavily. The 'r'names of variables/functions are actually regexes matching the appropriate names, and regexes
    determine the input format of function variables and 'set_var' actions. These make the input formats of the functions more flexible, and
    rnames serve as the identifiers of variables/functions later on. Some common input-formatting-regexes are provided in match_patterns, and
    their respective converter functions are available as static functions.
    'help' and 'exit' functions are already defined, and work properly.
    Class variables:
    match_patterns: dict(str->str)
        Some common regex strings that match usual input: booleans and text for example.
    _kwarg_pattern: compiled regex
        Matches a single keyword argument, and extracts the name and input from it. For internal use.
    _kwargs_pattern: compiled regex
        Matches the **kwargs part of a function call. For internal use.'''
    match_patterns = {'bool': r'(?:true|True|TRUE|false|False|FALSE)',
    'OnOff': r'(?:on|On|ON|off|Off|OFF)',
    'BoolOnOff': r'(?:true|True|TRUE|false|False|FALSE|on|On|ON|off|Off|OFF)',
    'text': r'''[^'"\s]\S*|'.+?(?<!\\)(?:\\\\)*'|".+?(?<!\\)(?:\\\\)*"'''}
    _kwarg_pattern = re.compile(r'''\s+(?P<name>\w+)=(?:(?P<v1>[^'"]\S*)|(?P<quote>['"])(?P<v2>(?:(?!(?P=quote)|\\).|\\(?P=quote))+)(?P=quote))[,;]?''')
    _kwargs_pattern = re.compile(r'''(?:\s+\w+=(?:[^'"]\S*|(?P<quote>['"])(?:(?!(?P=quote)).|\\(?P=quote))+(?P=quote))[,;]?)*\s*$''')

    def __init__(self, cursor='> ', reply_to_nonsense='', help_cmd='help', exit_cmd=r'quit|exit', 
        description=None, welcome_text="<Type 'help' for help.>"):
        '''cursor: str
            String displayed in the input prompt.
        reply_to_nonsense: str
            What will be printed, when the input is not a recognised command. No newline will be added at the end.
        help_cmd: str (regex)
            rname of the help command. If None, the built-in help will be disabled.
        exit_cmd: str (regex)
            rname of the exit command. If None, the built-in exit function will be disabled.
        description: str or None
            A short description of what this interactive app does. This will be printed at the beginning of 'help' calls.
        welcome_text: str
            This will be printed before the first input request.'''
        self.vars = []
        self.funcs = []
        self.cursor = cursor
        self.reply_to_nonsense = reply_to_nonsense
        self.help_cmd = help_cmd
        self.exit_cmd = exit_cmd
        self.description = description
        self.welcome_text = welcome_text
        self.started = False
        if help_cmd is not None:
            self.add_function(help_cmd,[],has_args=True,description=
            'If no parameters are given, display help for all commands and variables. Otherwise display help only for the given objects.')
        if exit_cmd is not None:
            self.add_function(exit_cmd,[],description='Exit the program.')
    
    def add_variable(self, rname, variable_pattern, description=''):
        '''Add a variable that can be parsed by the interpreter.
        rname: str
            Regex pattern that matches the name of this variable
        variable_pattern: str
            Regex pattern that describes how the input should be formatted. Contains a single group, which will be returned when we
            set the variable.'''
        self.vars.append({'rname': rname,
            'variable_pattern': variable_pattern,
            'description': re.sub(r'\n',r'\n\t',description),
            'name_pattern': re.compile(rname),
            'get_pattern': re.compile(rname+r'\s*'),
            'set_pattern': re.compile(rname+r'(?:\s*=\s*|\s+?)('+variable_pattern+')\s*')})
    
    def add_function(self, rname, signature, *flags, has_args=False, has_kwargs=False, description=''):
        '''Add a function that can be parsed by the interpreter.
        rname: str
            Regex pattern that matches this command (e.g. r'k[-_]opt(imi[sz]ation)?')
        signature: list[tuple(rname, variable_pattern[, default_value])]
            Function signature. Each element of the list represents a parameter with a tuple, whose first entry is a Regex-name
            for the variable, the second is a pattern for the argument (the entire matched pattern will be returned), and the third 
            (optional) one the default value.
        has_args: bool
            Does this function have an *args argument?
        has_kwargs: bool
            Does this function have a **kwargs argument?
        *flags: strings
            Possible flags for the function (Regex-names).'''
        self.funcs.append({'rname': rname, 
            'signature': signature, 
            'has_args': has_args, 
            'has_kwargs': has_kwargs, 
            'description': re.sub(r'\n',r'\n\t',description),
            'flags': flags,
            'name_pattern': re.compile(rname),
            'pattern_args': re.compile(rname+\
                (r'(?:\s+'+r'|\s+'.join((f'(?P<flag_{i}>{flag})[,;]?' for i, flag in enumerate(flags)))+')*' if len(flags)>0 else '')+\
                ''.join((f'(?:\s+(?P<arg_{i}>{t[1]})[,;]?' for i, t in enumerate(signature) if len(t)==2))+\
                ''.join((f'(?:\s+(?P<arg_{i}>{t[1]})[,;]?' for i, t in enumerate(signature) if len(t)==3))+r')?'*len(signature)+\
                r'(?:\s+'+r'|\s+'.join((t[0]+r'(?:\s*=\s*|\s+)'+f'(?P<kwarg_{i}>{t[1]})[,;]?' for i, t in enumerate(signature)))+')*')})
    
    def input(self):
        '''Request input and return it for further processing.'''
        if not self.started:
            self.started = True
            if self.welcome_text is not None and self.welcome_text != '':
                print(self.welcome_text)
        return self.parse(input(self.cursor))

    def parse(self, string):
        '''Parse a string and decode it into a variable assignment or a function call.
        If it is a variable name without parameters, it will return 
            'get_var', rname, None
        If it is a variable name with a properly formatted parameter, it will return
            'set_var', rname, contents_of_the_first_group
        If it is a variable name with an improperly formatted parameter, it will print an error, and return
            'fail_var', raname, input_string
        If it is a function name, than the first few arguments will be matched against the function's flags. The remaining parameters
        will be parsed in a python-function-pattern-style, with spaces between arguments. This means that the next few parameters will
        be considered positional input and matched against the respective input-patterns. Additional parameters will go into *args.
        name=value assignments can also set parameters, and unknown names will be passed to **kwargs.
        If the input is properly formatted, it will return
            'func', rname, {'flags': {flag_rname_0: bool, flag_rname_1: bool, ...},
                'params': {param_rname_0: str, param_rname_1: str, ...}[,
                '*args': [additional_arg_0, additional_arg_1, ...],
                '**kwargs': {name_0: str, name_1: str, ...}]}
        If the input is improperly formatted, it will print an error, and return:
            'fail_func', rname, input_string
        If the input doesn't match any of the variables/functions, it will return:
            'nonsense', None, None'''
        # Match variables
        for v in self.vars:
            if v["name_pattern"].match(string) is not None:
                if v["get_pattern"].fullmatch(string) is not None:
                    return 'get_var', v["rname"], None
                m = v["set_pattern"].fullmatch(string)
                if m is not None:
                    return 'set_var', v["rname"], m.group(1)
                print(f"ERROR: could not parse input. Please use {solve_regex(v['rname'])}=<value>, with both sides formatted properly.")
                return 'fail_var', v["rname"], string
        # Match functions
        for f in self.funcs:
            if f["name_pattern"].match(string) is not None:
                m = f["pattern_args"].match(string)
                if m is not None:
                    raw = m.groupdict()
                    ret = {"flags": {flag: (raw[f'flag_{i}'] is not None) for i, flag in enumerate(f["flags"])}} # get flags
                    # get params:
                    params = {}
                    for i, t in enumerate(f['signature']):
                        if raw[f'arg_{i}'] is not None:
                            params[t[0]] = raw[f'arg_{i}']
                        elif raw[f'kwarg_{i}'] is not None:
                            params[t[0]] = raw[f'kwarg_{i}']
                        elif len(t) == 3:
                            params[t[0]] = t[2]
                        else:
                            print(f'ERROR: argument {i} is not provided! Use the following signature:')
                            print('\t',self.short_func_signature(f))
                            return 'fail_func', f['rname'], string
                    ret['params'] = params
                    string = f['pattern_args'].sub('',string,count=1)
                    # get kwargs:
                    if f['has_kwargs']:
                        kwstring = ConsoleApp._kwargs_pattern.search(string)
                        ret['kwargs'] = {m.group('name'): m.group('v1') if m.group('v1') is not None else m.group('v2') 
                            for m in ConsoleApp._kwarg_pattern.finditer(kwstring.group(0))}
                        string = ConsoleApp._kwargs_pattern.sub('',string,count=1)
                    # get args:
                    if f['has_args']:
                        ret['args'] = string.split()
                        string = ''
                    # error:
                    if string != '':
                        print("ERROR: could not parse input. Superfluous parameters detected. Use the following signature:")
                        print('\t',self.short_func_signature(f))
                        return 'fail_func', f['rname'], string
                    # SUCCESS, do the thingy!!!
                    if f['rname'] == self.help_cmd:
                        self.help_func(*ret['args'])
                    elif f['rname'] == self.exit_cmd:
                        raise StopIteration
                    return 'func', f['rname'], ret
                else:
                    print('ERROR: could not parse input. Incorrect function signature detected. Use the following signature:')
                    print('\t',self.short_func_signature(f))
                    return 'fail_func', f['rname'], string
        # Do nothing
        print(self.reply_to_nonsense,end='')
        return 'nonsense', None, None

    def __call__(self, string):
        return self.parse(string)
    def __iter__(self):
        return self
    def __next__(self):
        return self.input()
    
    def short_func_signature(self, f):
        '''Create a short scheme for the function signature.'''
        return f"{solve_regex(f['rname'])}"+\
            (f" [flags: {', '.join((solve_regex(flag) for flag in f['flags']))}]" if len(f["flags"])>0 else '')+\
            ''.join((f" <{solve_regex(t[0])}>" for t in f['signature'] if len(t)==2))+\
            ''.join((f" <{solve_regex(t[0])}={t[2]}>" for t in f['signature'] if len(t)==3))+\
            (' *args' if f['has_args'] else '')+\
            (' **kwargs' if f['has_kwargs'] else '')
    
    def help_func(self, *args):
        '''Display help for the app if args is empty, otherwise for the given variables and functions.'''
        if len(args) == 0:
            if self.description is not None and self.description != '':
                print(self.description)
            print('===VARIABLES===')
            for v in self.vars:
                print(f"{solve_regex(v['rname'])}:")
                print(f"\t{v['description']}")
            print('===FUNCTIONS===')
            for f in self.funcs:
                print(f'{self.short_func_signature(f)}:')
                print(f"\t{f['description']}")
        else:
            for a in args:
                for v in self.vars:
                    if v['name_pattern'].fullmatch(a):
                        print(f"{solve_regex(v['rname'])}: variable")
                        print(f"\t{v['description']}")
                for f in self.funcs:
                    if f['name_pattern'].fullmatch(a):
                        print(f'{self.short_func_signature(f)}: function')
                        print(f"\t{f['description']}")
    # UTIL
    @staticmethod
    def get_text(s):
        '''Returns the text contained in s, with the quotes and escapes removed.'''
        if s[0] in '\'"':
            s = s[1:-1]
        s = re.sub(r'\\n','\n',s)
        return re.sub(r'\\(?P<a>)','\g<a>',s)
    @staticmethod
    def str_to_bool(s):
        '''Returns which boolean value this string represents (true,false,on,off).'''
        if re.match(r'true|True|TRUE|on|On|ON',s) is not None:
            return True
        elif re.match(r'false|False|FALSE|off|Off|OFF',s) is not None:
            return False
        else:
            raise ValueError(f'{s} is not a properly formatted boolean!')
    

def solve_regex(pattern_string):
    '''Return a "typical" string which satisfies the given (not-too-complicated) regex.
    Can deal with (?:), [], \s\d\w\S\D\W, ., ?, +, *, |'''
    def process_brackets(match):
        '''Processes the contents of a match for a [...] instance. Supposes that \s\w\d\S\D\W have been replaced, but *+?\ have not.'''
        if match.group('c')[0] == r'\\':
            return match.group('b') + match.group(0)[1]
        elif match.group('c')[0] != r'^':
            return match.group('b') + match.group('c')[0]
        else:
            p = re.compile(f'[{match.group("c")}]')
            for i in range(32, 127):
                if p.match(chr(i)) is not None:
                    return match.group('b') + chr(i)
            for c in '\n\t':
                if p.match(c) is not None:
                    return match.group('b') + c
    #   even \-s: (?P<b>(?:[^\\]|^)(?:\\\\)*)
    #   no starting (: (?!(?:[^\\]|^)(?:\\\\)*\().
    #   characters without (: (?:(?!(?:[^\\]|^)(?:\\\\)*\().)*
    s = re.sub(r'(?P<b>(?:[^\\]|^)(?:\\\\)*)(?:\\s|\.|\\W)',r'\g<b> ',pattern_string) # \s,\W,. -> ' '
    s = re.sub(r'(?P<b>(?:[^\\]|^)(?:\\\\)*)(?:\\d)',r'\g<b>0',s) # \d -> 0
    s = re.sub(r'(?P<b>(?:[^\\]|^)(?:\\\\)*)(?:\\S|\\w|\\D)',r'\g<b>a',s) # \S, \w, \D -> a
    s = re.sub(r'(?P<b>(?:[^\\]|^)(?:\\\\)*)\[(?P<c>\].*?(?<!\\)(?:\\\\)*|.*?[^\\](?:\\\\)*)\]',process_brackets,s) # replace []-s with 
    s = re.sub(r'(?P<b>(?:[^\\]|^)(?:\\\\)*)(?:\*|\+)',r'\g<b>',s) # *, + -> ''
    s = re.sub(r'(?P<b>(?:[^\\]|^)(?:\\\\)+)\?',r'\g<b>',s) # \\\\..\\? -> \\\\..\\        now all ?-s are escaped or are preceded by other characters
    s = re.sub(r'(?P<b>(?:[^\\]|^)(?:\\\\)*\\\(|[^\\\(])\?',r'\g<b>',s) # a? -> a       # now all ?-s are escaped; only ?,),(,| may be escaped now
    while True:
        old_s = s
        s = re.sub(r'(?P<b>(?:[^\\]|^)(?:\\\\)*)(?P<lhs>\|(?:(?!(?:[^\\]|^)(?:\\\\)*\().)*?(?<!\\)(?:\\\\)*)(?=\||\)|$)',r'\g<b>',s) # remove |-s
        #s = re.sub(r'(?P<b>(?:[^\\]|^)(?:\\\\)*)\((?!\?)(?P<c>(?:(?!(?:[^\\]|^)(?:\\\\)*\().)*?)\)',r'\g<b>\g<c>',s) # remove ()-s
        s = re.sub(r'(?P<b>(?:[^\\]|^)(?:\\\\)*)\(\?:(?P<c>(?:(?!(?:[^\\]|^)(?:\\\\)*\().)*?(?<!\\)(?:\\\\)*)\)',r'\g<b>\g<c>',s) # remove (?:...)-s
        if s == old_s:
            break
    s = re.sub(r'\\(?P<c>.)',r'\g<c>',s) # remove \ from escaped characters
    return s

if __name__ == '__main__':
    app = ConsoleApp(description='SAMPLE CONSOLE APP\nThis app is meant to show how this library operates. After each command, the resulting tuple will be printed.')
    app.add_function(r'[rR]epeat',[(r'text',ConsoleApp.match_patterns['text']),(r'n(?:umber)?',r'\d+','1')],
        description="Prints 'text' to the output stream 'number' times.")
    app.add_variable(r'var(?:iable)?','\d+','Generic variable containing a nonnegative integer.')
    v = 0
    for action, rname, data in app:
        if action == 'func' and rname == r'[rR]epeat':
            for _ in range(int(data['params'][r'n(?:umber)?'])):
                print(ConsoleApp.get_text(data['params'][r'text']))
        elif action == 'get_var' and rname == r'var(?:iable)?':
            print(v)
        elif action == 'set_var' and rname == r'var(?:iable)?':
            v = int(data)
        print(f"\n| action: {action}; rname: {rname}; data: {data}")