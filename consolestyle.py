import colorama
colorama.init()
class style:
    '''Collection of characters that change the style of the text when printed to the console. 
    `UN` means clear that type of formatting. `ENDC` clears all formatting.'''
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    REVERSE = '\033[7m'
    HIDE = '\033[8m'
    CROSSOUT = '\033[9m'
    UNBOLD = '\033[22m'
    UNITALIC = '\033[23m'
    UNUNDERLINE = '\033[24m'
    UNHIDE = '\033[28m'
    UNCROSS = '\033[29m'
class fclr:
    '''Collection of characters that change the foreground color when printed to the console. 
    `DEFAULT` is the default color, `ENDC` clears all formatting. `B` means "bright".'''
    ENDC = '\033[0m'
    DEFAULT = '\033[39m'
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BBLACK = '\033[90m'
    BRED = '\033[91m'
    BGREEN = '\033[92m'
    BYELLOW = '\033[93m'
    BBLUE = '\033[94m'
    BMAGENTA = '\033[95m'
    BCYAN = '\033[96m'
    BWHITE = '\033[97m'
    @staticmethod
    def n(number):
        '''Return one of 256 predefined foreground colors.
        0   - 7:   standard colors
        8   - 15:  high intensity colors
        16  - 231: 6×6×6 cube
        232 - 255: grayscale from black to white'''
        return '\033[38;5;'+str(number)+'m'
    @staticmethod
    def rgb(r, g, b):
        '''Specify a foreground color by RGB (0-255) values.'''
        return '\033[38;2;'+f'{r};{g};{b}m'
class bclr:
    '''Collection of characters that change the background color when printed to the console. 
    `DEFAULT` is the default color, `ENDC` clears all formatting. `B` means "bright".'''
    ENDC = '\033[0m'
    DEFAULT = '\033[49m'
    BLACK = '\033[40m'
    RED = '\033[41m'
    GREEN = '\033[42m'
    YELLOW = '\033[43m'
    BLUE = '\033[44m'
    MAGENTA = '\033[45m'
    CYAN = '\033[46m'
    WHITE = '\033[47m'
    BBLACK = '\033[100m'
    BRED = '\033[101m'
    BGREEN = '\033[102m'
    BYELLOW = '\033[103m'
    BBLUE = '\033[104m'
    BMAGENTA = '\033[105m'
    BCYAN = '\033[106m'
    BWHITE = '\033[107m'
    @staticmethod
    def n(number):
        '''Return one of 256 predefined background colors.
        0   - 7:   standard colors
        8   - 15:  high intensity colors
        16  - 231: 6×6×6 cube
        232 - 255: grayscale from black to white'''
        return '\033[48;5;'+str(number)+'m'
    @staticmethod
    def rgb(r, g, b):
        '''Specify a background color by RGB (0-255) values.'''
        return '\033[48;2;'+f'{r};{g};{b}m'

if __name__ == "__main__":
    print("asd",fclr.GREEN, "qwe")