from typing import TypeVar
# Use Generic with Dict
k = TypeVar('k')
v = TypeVar('v')

def get_item(container : dict[k,v],key : k) -> v :
    return container[key]

d = {'a':2,'b':6}
value = get_item(d,'a') # return int
print(value)
