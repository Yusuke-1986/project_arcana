def subjecto():
    i = 1
    __i = 0
    __prima = 100
    while ((i < 10)) and (__i < __prima):
        if ((i % 15) == 0):
            print("FizzBuzz")
        else:
            pass
        if ((i % 3) == 0):
            print("Fizz")
        else:
            pass
        if ((i % 5) == 0):
            print("Buzz")
        else:
            print(i)

        i = (i + 1)

        if (i > 100):
            print("end.")
            break
        else:
            pass
        __i += 1

if __name__=="__main__":
    subjecto()