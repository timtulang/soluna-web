\\\ DAY 1, Problem 5: Display multiplication table based on row and column input

nova("=== Multiplication Table Generator ===");
nova("Enter number of rows:");
kai rows = lumina();

nova("Enter number of columns:");
kai cols = lumina();

nova("========== MULTIPLICATION TABLE ==========");

\\ Loop through rows
phase kai i = 1, rows, 1
    \\ Loop through columns
    phase kai j = 1, cols, 1
        kai product = i * j;
        lumen(product .. " ");
    mos
    nova("");
mos
