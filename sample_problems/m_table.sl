lumen("Enter number of rows:");
kai rows = lumina();
lumen("Enter number of columns:");
kai cols = lumina();

kai rlimit = rows + 1;
kai climit = cols + 1;

phase kai r = 1, rlimit, 1 cos
    phase kai c = 1, climit, 1 cos
        kai prod = r * c;
        nova(prod .. " ");
    mos
    lumen("");
mos