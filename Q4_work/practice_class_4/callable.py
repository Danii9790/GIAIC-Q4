from dataclasses import dataclass
from typing import Callable
# Callable ka matlab hai: "Ek function jo 2 numbers lega aur string dega."
# A Callable that takes two integers and return a string
MyFunType = Callable[[int,int],str]
print(MyFunType)

# Usage
@dataclass
# class Calculator:
#     operation : Callable[[int,int],str]

#     def calculate(self,a : int ,b : int) -> str:
#         return self.operation(a,b)
    
# def add_and_stringify(x: int, y: int) -> str:
#     return str(x + y)

# calc=Calculator(operation=add_and_stringify)
# print(calc.calculate(5,12))

class Calcultor:
    operation : Callable[[int,int],str]

    def __call__(self, a: int , b: int) ->str:
        return self.operation(a,b)

def add_and_stringify(x : int,y : int) ->str :
    return str(x + y)
calc=Calcultor(operation=add_and_stringify)
print(calc(4,6))

        
    