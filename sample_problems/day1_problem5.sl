\\\ DAY 1, Problem 5: Display multiplication table based on row and column input

nova("=== Multiplication Table Generator ===");
nova("Enter number of rows:");
kai rows = lumina();
rows += 1;

nova("Enter number of columns:");
kai cols = lumina();
cols += 1;

nova("========== MULTIPLICATION TABLE ==========");

\\ Loop through rows
phase kai i = 1, rows, 1 cos
    \\ Loop through columns
    phase kai j = 1, cols, 1 cos
        kai product = i * j;
        lumen(product .. " ");
    mos
    nova("");
mos
