\\\ DAY 3, Problem 1: Area of different shapes (Circle, Triangle, Square, Rectangle)

nova("=== Area Calculator ===");
nova("Menu:");
nova("1. Area of Circle");
nova("2. Area of Triangle");
nova("3. Area of Square");
nova("4. Area of Rectangle");
nova("Choose shape (1-4):");
kai choice = lumina();

sol choice == 1
    \\\ Circle: Area = PI * r^2
    nova("Enter radius:");
    kai radius = lumina();
    kai area = 314 * radius * radius / 100;
    nova("Area of circle: " .. area);
mos
soluna choice == 2
    \\\ Triangle: Area = (base * height) / 2
    nova("Enter base:");
    kai base = lumina();
    nova("Enter height:");
    kai height = lumina();
    kai area = base * height / 2;
    nova("Area of triangle: " .. area);
mos
soluna choice == 3
    \\\ Square: Area = side * side
    nova("Enter side:");
    kai side = lumina();
    kai area = side * side;
    nova("Area of square: " .. area);
mos
soluna choice == 4
    \\\ Rectangle: Area = length * width
    nova("Enter length:");
    kai length = lumina();
    nova("Enter width:");
    kai width = lumina();
    kai area = length * width;
    nova("Area of rectangle: " .. area);
mos
luna
    nova("Invalid Input!");
mos

return void;
