void printNaturals(kai n, kai limit)
    sol n <= limit
        lumen(n .. "\n");
        printNaturals(n + 1, limit);
    mos
    zara;
mos

nova("=== First 50 Natural Numbers (Recursive) ===");
nova("The natural numbers are: ");
printNaturals(1, 50);
nova("");
