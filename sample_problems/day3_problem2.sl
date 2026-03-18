\\\ DAY 3, Problem 2: Area calculations with separate functions

flux circleArea(kai radius) {
    \\\ Area = PI * r^2
    let area = 314 * radius * radius / 100;
    return area;
}

flux triangleArea(kai base, kai height) {
    \\\ Area = (base * height) / 2
    let area = base * height / 2;
    return area;
}

flux squareArea(kai side) {
    \\\ Area = side * side
    let area = side * side;
    return area;
}

flux rectangleArea(kai length, kai width) {
    \\\ Area = length * width
    let area = length * width;
    return area;
}

\\\ Main program
nova("=== Area Calculator with Functions ===");
nova("Menu:");
nova("1. Area of Circle");
nova("2. Area of Triangle");
nova("3. Area of Square");
nova("4. Area of Rectangle");
nova("Choose shape (1-4):");
kai choice = lumina();

sol choice == 1
    nova("Enter radius:");
    kai radius = lumina();
    kai result = circleArea(radius);
    nova("Area of circle: " .. result);
mos
soluna choice == 2
    nova("Enter base:");
    kai base = lumina();
    nova("Enter height:");
    kai height = lumina();
    kai result = triangleArea(base, height);
    nova("Area of triangle: " .. result);
mos
soluna choice == 3
    nova("Enter side:");
    kai side = lumina();
    kai result = squareArea(side);
    nova("Area of square: " .. result);
mos
soluna choice == 4
    nova("Enter length:");
    kai length = lumina();
    nova("Enter width:");
    kai width = lumina();
    kai result = rectangleArea(length, width);
    nova("Area of rectangle: " .. result);
mos
luna
    nova("Invalid Input!");
mos

return void;
