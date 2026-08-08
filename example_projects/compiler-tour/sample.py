rate = 2


def make_counter(start):
    total = start

    def bump(step=1):
        nonlocal total
        total += step * rate
        return total

    return bump


counter = make_counter(10)
print(counter())
print(counter(3))
