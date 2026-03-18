\\\ DAY 3, Problem 3B: Print first N natural numbers using recursion

flux printNaturals(kai n) {
    sol n > 0
        printNaturals(n - 1);
        nova(n .. " ");
    mos
    return void;
}

nova("=== First N Natural Numbers (Recursive) ===");
nova("Enter a number:");
kai n = lumina();
nova("First " .. n .. " natural numbers: ");
printNaturals(n);
nova("");

return void;
