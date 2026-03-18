\\\ DAY 3, Problem 3A: Print first 50 natural numbers using recursion

flux printNaturals(kai n, kai limit) {
    sol n <= limit
        nova(n .. " ");
        printNaturals(n + 1, limit);
    mos
    return void;
}

nova("=== First 50 Natural Numbers (Recursive) ===");
nova("The natural numbers are: ");
printNaturals(1, 50);
nova("");

return void;
