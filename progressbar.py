from time import sleep
from math import ceil
import sys
style = 1

try:
    from colorama import Fore, init
    init(autoreset=True)
except ImportError:
    errors.append("Не найден модуль 'colorama'! \nУстановите модуль коммандой pip install colorama ")
except Exception as e:
    errors.append(e)


class ProgresBar():
    def __init__(self, max_length=200, width=10):
        super(ProgresBar, self).__init__()
        self.length = max_length
        self.status = ''
        self.progress = 0 
        self.k  = width / max_length # Вычесляет маштаб
        self.px = 100 / max_length # Вычисляет % для заданого числа итераций


    def call(self):
        self.progress += 1
        if self.progress > self.length:
            raise StopIteration
        else:
            if self.progress == self.length:
                self.status = '\r\n'
            if style == 0:
                text = Fore.CYAN + '\r[%] [{}] {} % {}'.format( '\u25A0' * ceil(self.progress * self.k) + '-' * ceil((self.length - self.progress) * self.k), round(self.progress + self.px), self.status )
            if style == 1:
                text = Fore.CYAN + '\r[%] {} % {} {}'.format(round(self.progress * self.px),  '\u25A0' * ceil(self.progress * self.k),  self.status)
            sys.stdout.write(text)
            sys.stdout.flush()


def Progress(progress, max_length=200, width=25):    
    status =  ''
    k  = width / max_length # Вычесляет маштаб
    px = 100 / max_length # Вычисляет % для заданого числа итераций
    if progress <= max_length:
        if progress == max_length:
            status = '\r\n'
        if style == 0:
            text = '\r[{}] {}% {}'.format('\u25A0' * ceil(progress  * k) + '\u2014'  * ceil((max_length - progress) * k), round(progress * px), status)
        if style == 1:
            text = '\r {} % {} {}'.format(round(progress * px),  '\u25A0' * ceil(progress * k),  status)
        sys.stdout.write(text)
        sys.stdout.flush()
    else:
        sys.stdout.write('\r stoped!')
        sys.stdout.flush()
        raise StopIteration


if __name__ == '__main__':
    t = 2
    if t == 1:
        print('progress started')
        for i in range(1,300): 
            sleep(.1)
            try:
                Progress(i) 
            except StopIteration:
                break
    if t == 2:
        p = ProgresBar()
        for _ in range(1,1000000):
            sleep(.1)
            try:
                p.call()
            except StopIteration:
                break

        
        



    
