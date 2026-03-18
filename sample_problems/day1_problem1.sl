\\\ DAY 1, Problem 1: Input 2 numbers and show Sum, Difference, Product, Quotient

nova("=== Arithmetic Operations ===");
nova("Enter first number:");
kai num1 = lumina();

nova("Enter second number:");
kai num2 = lumina();

\\ Calculate operations
kai sum = num1 + num2;
kai difference = num1 - num2;
kai product = num1 * num2;
kai quotient = num1 / num2;

\\ Display results
nova("========== RESULTS ==========");
nova("Number 1: " .. num1);
nova("Number 2: " .. num2);
nova("Sum: " .. sum);
nova("Difference: " .. difference);
nova("Product: " .. product);
nova("Quotient: " .. quotient);
