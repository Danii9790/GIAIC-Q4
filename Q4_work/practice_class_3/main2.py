from dataclasses import dataclass


@dataclass
class Human:
    name : str
    age :int
    def greet(self):
        return f"Hi i am {self.name}"
    
    def works(self):
        return f"i am working"
    def __call__(self):  # (Dunder method)
        return f"Hello"
obj1=Human("Daniyal",21)
print(obj1.name)
print(obj1.age)
print(obj1.greet())
print(obj1.works())
print(obj1.__dict__)

