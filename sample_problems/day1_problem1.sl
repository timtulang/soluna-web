\\\ DAY 1, Problem 1: Input 2 numbers and show Sum, Difference, Product, Quotient

nova("=== Arithmetic Operations ===");
nova("Enter first number:");
flux num1 = lumina();

nova("Enter second number:");
flux num2 = lumina();

\\ Calculate operations
flux sum = num1 + num2;
flux difference = num1 - num2;
flux product = num1 * num2;
flux quotient = num1 / num2;

\\ Display results
nova("========== RESULTS ==========");
nova("Number 1: " .. num1);
nova("Number 2: " .. num2);
nova("Sum: " .. sum);
nova("Difference: " .. difference);
nova("Product: " .. product);
nova("Quotient: " .. quotient);
