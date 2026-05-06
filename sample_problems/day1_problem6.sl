nova("=== Shape Display Program ===");
nova("Menu:");
nova("1. Triangle");
nova("2. Inverted Triangle");
nova("3. Rectangle");
nova("4. Square");

nova("Choose shape (1-4):");
kai choice = lumina();

orbit choice < 1 || choice > 4 cos
    nova("Invalid choice! Please enter a number between 1 and 4:");
    choice = lumina();
mos

nova("Enter size/rows (positive integer only):");
kai size = lumina();

orbit size < 1 cos
    nova("Invalid size! Please enter a number greater than 0:");
    size = lumina();
mos

nova("========== SHAPE OUTPUT ==========");

sol choice == 1
    \\ Shifted limit to (size + 1)
    phase kai i = 1, (size + 1), 1 cos
        kai spaces = size - i;
        sol spaces > 0
            \\ Shifted limit to (spaces + 1)
            phase kai s = 1, (spaces + 1), 1 cos
                lumen(" ");
            mos
        mos
        
        kai stars = (i * 2);
        \\ Shifted limit to (stars + 1)
        phase kai j = 1, (stars + 1), 1 cos
            lumen("*");
        mos
        nova("");
    mos
mos
soluna choice == 2
    \\ Shifted limit to 0 so it includes row 1
    phase kai i = size, 0, -1 cos
        kai spaces = size - i;
        sol spaces > 0
            \\ Shifted limit to (spaces + 1)
            phase kai s = 1, (spaces + 1), 1 cos
                lumen(" ");
            mos
        mos
        
        kai stars = (i * 2);
        \\ Shifted limit to (stars + 1)
        phase kai j = 1, (stars + 1), 1 cos
            lumen("*");
        mos
        nova("");
    mos
mos
soluna choice == 3
    kai width = size + 5;
    \\ Shifted limits
    phase kai i = 1, (size + 1), 1 cos
        phase kai j = 1, (width + 1), 1 cos
            lumen("*");
        mos
        nova("");
    mos
mos
soluna choice == 4
    \\ Shifted limits
    phase kai i = 1, (size + 1), 1 cos
        phase kai j = 1, (size + 1), 1 cos
            lumen("* ");
        mos
        nova("");
    mos
mos