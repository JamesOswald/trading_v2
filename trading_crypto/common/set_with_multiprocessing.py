from multiprocessing import Manager

# weird assignment behaviour required by multiprocessing's manager.dict() as in: https://docs.python.org/2/library/multiprocessing.html
def set_with_multiprocessing(obj, value, key=None):
    temp_obj = obj
    if type(obj) == type(Manager().dict()) and key == 'dict_type':
        for k in value.keys():
            temp_obj[k] = value[k]
    elif type(obj) == type(Manager().dict()):
        temp_obj[key] = value
    elif type(obj) == type(Manager().list()):
        temp_obj.extend(value)
    return temp_obj
    
