func_list = []
for num in range(5):
    func_list.append(lambda x=num: func(x))

def func(thing):
    print(thing)

for f in func_list:
    f()