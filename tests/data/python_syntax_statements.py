assert a
assert a; assert b
raise RuntimeError
raise RuntimeError from e
return
return 1
return *a
del a
del a, b,
global a
global a, b
nonlocal a
nonlocal a, b
yield a
yield from a

for i in a:
    pass

for i in b:
    pass
else:
    pass

if a:
    pass
elif b:
    pass
else:
    pass

if a:
    pass
elif b:
    pass
elif c:
    pass

while s:
    pass

while False:
    pass
else:
    pass

for i in a:
    continue

for i in a:
    break

with a:
    pass

with a as b:
    pass

with (a, b,):
    pass

with (a as b, c):
    pass

try:
    pass
finally:
    pass

try:
    pass
except ValueError:
    pass
except (IndexError, RuntimeError,):
    pass
except Exception as e:
    pass
else:
    pass
finally:
    pass
