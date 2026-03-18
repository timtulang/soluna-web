\\\ DAY 2, Problem 3: Sum of the cube of numbers from 1 to N

nova("=== Sum of Cubes ===");
nova("Enter a number N:");
kai n = lumina();

\\\ Error checking: n must be positive
sol n <= 0
    nova("Error: Please enter a positive number!");
mos
luna
    kai sum = 0;
    
    phase kai i = 1, n, 1
        kai cube = i * i * i;
        sum = sum + cube;
    mos
    
    nova("Sum of cubes from 1 to " .. n .. " is " .. sum);
mos
