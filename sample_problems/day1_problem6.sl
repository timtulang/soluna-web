\\\ DAY 1, Problem 6: Display shapes with asterisks (Triangle, Inverted Triangle, Rectangle, Square)

nova("=== Shape Display Program ===");
nova("Menu:");
nova("1. Triangle");
nova("2. Inverted Triangle");
nova("3. Rectangle");
nova("4. Square");
nova("Choose shape (1-4):");
kai choice = lumina();

nova("Enter size/rows:");
kai size = lumina();

nova("========== SHAPE OUTPUT ==========");

sol choice == 1
    \\ Triangle
    phase kai i = 1, size, 1
        phase kai j = 1, i, 1
            lumen("*");
        mos
        nova("");
    mos
mos
soluna choice == 2
    \\ Inverted Triangle
    phase kai i = size, 1, -1
        phase kai j = 1, i, 1
            lumen("*");
        mos
        nova("");
    mos
mos
soluna choice == 3
    \\ Rectangle
    phase kai i = 1, size, 1
        phase kai j = 1, size + 2, 1
            lumen("*");
        mos
        nova("");
    mos
mos
soluna choice == 4
    \\ Square
    phase kai i = 1, size, 1
        phase kai j = 1, size, 1
            lumen("*");
        mos
        nova("");
    mos
mos
luna
    nova("Invalid choice!");
mos
