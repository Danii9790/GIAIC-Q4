from typing import Generic,TypeVar,ClassVar
from dataclasses import dataclass,field

# Type variable for Generic typing
T =TypeVar('T')

@dataclass
class Stack(Generic[T]):
    # Instance Level  ==> obj = Stack
    items : list[T] =field(default_factory=list) 
    # Class Level ==> same are places
    limit : ClassVar[int] = 10

    def push(self,item:T) -> None :
        self.items.append(item)
    def pop(self) -> T:
        return self.items.pop()
    
