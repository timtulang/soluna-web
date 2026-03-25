nova("=== Area Calculator ===");
nova("Menu:");
nova("1. Area of Circle");
nova("2. Area of Triangle");
nova("3. Area of Square");
nova("4. Area of Rectangle");

nova("Choose shape (1-4):");
kai choice = lumina();

\\ Trap invalid menu choices
orbit choice < 1 || choice > 4 cos
    nova("Invalid choice! Please enter a number between 1 and 4:");
    choice = lumina();
mos

sol choice == 1
    \\ Circle: Area = PI * r^2
    nova("Enter radius:");
    flux radius = lumina();
    
    orbit radius <= 0 cos
        nova("Radius must be greater than 0. Enter radius:");
        radius = lumina();
    mos
    
    flux area = 3.14 * (radius ^ 2);
    nova("Area of circle: " .. area);
mos
soluna choice == 2
    \\ Triangle: Area = (base * height) / 2
    nova("Enter base:");
    flux base = lumina();
    
    orbit base <= 0 cos
        nova("Base must be greater than 0. Enter base:");
        base = lumina();
    mos
    
    nova("Enter height:");
    flux height = lumina();
    
    orbit height <= 0 cos
        nova("Height must be greater than 0. Enter height:");
        height = lumina();
    mos
    
    \\ Using / gives exact float division
    flux area = (base * height) / 2.0;
    nova("Area of triangle: " .. area);
mos
soluna choice == 3
    \\ Square: Area = side * side
    nova("Enter side:");
    flux side = lumina();
    
    orbit side <= 0 cos
        nova("Side must be greater than 0. Enter side:");
        side = lumina();
    mos
    
    flux area = side * side;
    nova("Area of square: " .. area);
mos
soluna choice == 4
    \\ Rectangle: Area = length * width
    nova("Enter length:");
    flux length = lumina();
    
    orbit length <= 0 cos
        nova("Length must be greater than 0. Enter length:");
        length = lumina();
    mos
    
    nova("Enter width:");
    flux width = lumina();
    
    orbit width <= 0 cos
        nova("Width must be greater than 0. Enter width:");
        width = lumina();
    mos
    
    flux area = length * width;
    nova("Area of rectangle: " .. area);
mos