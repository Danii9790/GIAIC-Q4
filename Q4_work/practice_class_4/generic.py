"""
Generic let's you create functions,method,or classes that can work with multiple types while preserving type relationship . (Generic) 
1. Better communicate the intent of your code.
2. Allow static type checking to verify correctness.
"""
from typing import TypeVar
# Use Generic Type on Run Time . In case of user there is no idea user input data type is what?
# Analogy --> Think of T as fill in the Blank
# Type variable for generic typing
T = TypeVar('T')

def generic_first_element(items : list[T]) -> T:
    return items[0]

nums = [2,4,6,8]
strings = ["a","b","c","d"]

num_result = generic_first_element(nums)           # Type inferred as int
string_result = generic_first_element(strings)     # Type inferred as str

print(num_result)
print(string_result)

# EXAMPLE : Without Generic
from typing import Any
# ISSUE : Any --> I don't khown the data type.
def generic_first_element(items : list[Any]) -> Any:
    return items[0]

num = [2,4,6,5]
string = ["a","b","c","d"]

num_result = generic_first_element(num)
string_result = generic_first_element(string)

print(num_result)
print(string_result)
# Issue : No type checking . We can't restrict or inform about expected data type explicity.



# Pydantic Example : Pydantic aisi library hai jo Python objects (models) banati hai aur unmein automatically data validate karti hai based on type hints.

# from pydantic import BaseModel

# class User(BaseModel):
#     name: str
#     age: int
#     email: str

# # Correct data
# user = User(name="Daniyal", age=22, email="daniyal@example.com")
# print(user)

# # Wrong data (age as string, which should be int)
# user2 = User(name="Ali", age="twenty", email="ali@example.com")  # ❌ Will raise error!



