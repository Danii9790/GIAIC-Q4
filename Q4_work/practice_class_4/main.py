from dataclasses import dataclass,field

# Ye code har insaan ke liye naam, umar, optional email aur ek alag list deta hai — jisme hum uski qualities likh sakte hain.
# GOOD EXAMPLE : Simple dataclass with type hints
@dataclass
class Person :
    # __repr__: str = "Person(name={self.name} , age={self.age})"  | this is called Dunder method this method is automatically written by @dataclass
    name : str
    age : int
    email : str | None = None
    # Using field() with default_factory for mutable default values
    tags : list[str] = field(default_factory=list)

    def is_adult(self) -> bool:
        "Example Method that uses the dataclass attributes."
        return self.age >= 18

# Usage Example 
def demo_good_usage():
    # Creating instance
    person1 = Person("Daniyal",21,"daniyalashraf9790@gmail.com")
    person2 = Person("Ahmed",8)
    person3 = Person("Jamal",25,tags=["student","part_time_bussiness"])

    # Adding to a mutable field
    person1.tags.append("Developer")

    # Using the build-in string representation
    print(f"Person 1 : {person1}")
    print(f"Person 2 : {person2}")
    print(f"Person 3 : {person3}")

    # Using the instance method
    print(f"Is {person1.name} an adult? {person1.is_adult()} ")
    print(f"Is {person2.name} an adult? {person2.is_adult()} ")
    print(f"Is {person3.name} an adult? {person3.is_adult()}")

demo_good_usage()


# BAD EXAMPLE : Class without dataclass
class PersonBad:
    def __init__(self,name,age,email=None,tags=None):
        self.name = name
        self.age = age
        self.email = email
        # Common Mistake : mutable default
        self.tags = tags if tags is not None else []
    
    # Have to manually define string representation
    def __repr__(self) :
        return f"PersonBad (name = {self.name},age={self.age},email={self.email},tags={self.tags}) "
    # Have manually define equality
    def __eq__(self,other) :
        if not isinstance(other,PersonBad) :
            return False
        return (self.name == other.name and 
                self.age == other.age and
                self.email == other.email and 
                self.tags == other.tags)

def demo_bad_usage():
    person1 = PersonBad("Alice",16,"xyz@gmail.com")
    person2 = PersonBad("Jhon",16)

    print(f"Person 1 : {person1}")
    print(f"Person 2 : {person2}")
        
        

demo_bad_usage()


# Core features of OpenAI-SDK Vender locking ==> Means chatcompletionsmodel (connective for other llm or models)
