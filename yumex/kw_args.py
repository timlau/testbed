

def func(*args, **kwargs):
    print(kwargs.pop("dummy", "default"))
    
    
func()
func(dummy="tim")