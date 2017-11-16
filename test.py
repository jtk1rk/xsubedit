import random
class test:
    def __init__(self):
        a = random.random()

a = [test() for i in range(5)]
print(a)
