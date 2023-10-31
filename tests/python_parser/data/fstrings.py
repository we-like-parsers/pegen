a = 10
f'{a * x()}'



f'no formatted values'
f'eggs {a * x()} spam {b + y()}'



a = 10
f'{a * x()} {a * x()} {a * x()}'



a = 10
f'''
  {a
     *
       x()}
non-important content
'''



a = f'''
          {blech}
    '''



x = (
    f" {test(t)}"
)



x = (
    u'wat',
    u"wat",
    b'wat',
    b"wat",
    f'wat',
    f"wat",
)
y = (
    u'''wat''',
    u"""wat""",
    b'''wat''',
    b"""wat""",
    f'''wat''',
    f"""wat""",
)



x = (
        'PERL_MM_OPT', (
            f'wat'
            f'some_string={f(x)} '
            f'wat'
        ),
)



f'{expr:}'
f'{expr:d}'
foo = 3.14159
verbosePrint(f'Foo {foo:.3} bar.')
