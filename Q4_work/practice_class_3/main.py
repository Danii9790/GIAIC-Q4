from dataclasses import dataclass
from typing import ClassVar

@dataclass   # @dataclass aik aisa shortcut hai jo class ka __init__ aur kuch methods khud bana deta hai.

class American:
    name : str   # Instance variable (different for every object)
    age : int
    weight : float
    language : ClassVar[str] = "English"  #Class variable (same for all Amercian) and (ClassVar[str]) [] is called generic.
    # Instance function
    def speaks(self):
        return f"{self.name} is Speaking...{American.language}"
    def eat(self):
        return f"{self.name} is eating..."
    @staticmethod  #  You can call it without making an object.
    def country_language():
        return American.language
    
jhon=American(name="Daniyal",age=21,weight=50)
print(jhon.speaks())
print(jhon.eat())
print(American.country_language())
    
