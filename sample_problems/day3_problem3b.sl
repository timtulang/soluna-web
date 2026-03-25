void printNaturals(kai n)
    sol n > 0
        printNaturals(n - 1);
        lumen(n .. " ");
    mos
    zara;
mos

nova("=== First N Natural Numbers (Recursive) ===");
nova("Enter a number:");
kai n = lumina();

\\ Trap invalid input
orbit n <= 0 cos
    nova("Please enter a number greater than 0:");
    n = lumina();
mos

lumen("First " .. n .. " natural numbers: ");
printNaturals(n);
nova("");