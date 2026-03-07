lumen("Enter row size for shapes:");
kai size = lumina();
kai sizelimit = size + 1;

lumen("Triangle:");
phase kai i = 1, sizelimit, 1 cos
    kai spaces = size - i;
    phase kai s = 0, spaces, 1 cos
        nova(" ");
    mos
    kai l = i + 1;
    phase kai j = 1, l, 1 cos
        nova("* ");
    mos
    lumen("");
mos

lumen("Inverted Triangle:");
phase kai i = size, 0, -1 cos
    kai spaces = size - i;
    phase kai s = 0, spaces, 1 cos
        nova(" ");
    mos
    kai l = i + 1;
    phase kai j = 1, l, 1 cos
        nova("* ");
    mos
    lumen("");
mos

lumen("Rectangle:");
kai rectwidth = size + 3;
phase kai i = 1, sizelimit, 1 cos
    phase kai j = 1, rectwidth, 1 cos
        nova("* ");
    mos
    lumen("");
mos

lumen("Square:");
phase kai i = 1, sizelimit, 1 cos
    phase kai j = 1, sizelimit, 1 cos
        nova("* ");
    mos
    lumen("");
mos