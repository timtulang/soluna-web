lumen("Enter length of series:");
kai n = lumina();
kai nlimit = n + 1;

kai a = 0;
kai b = 1;
kai nextTerm = 0;

lumen("Fibonacci Sequence:");
phase kai i = 1, nlimit, 1 cos
    sol i == 1
        nova(a .. " ");
    mos
    soluna i == 2
        nova(b .. " ");
    mos
    luna
        nextTerm = a + b;
        a = b;
        b = nextTerm;
        nova(nextTerm .. " ");
    mos
mos
lumen("");