nova("=== Problem 4: Valid Username ===");
lani isValid = sage;

orbit isValid == sage cos
    nova("Enter a username:");
    selene uname = lumina();
    kai length = #uname;
    
    sol length < 8
        nova("Must be at least 8 characters.");
    mos
    luna
        lani hasUpper = sage;
        lani hasLower = sage;
        lani hasNum = sage;
        lani hasSpec = sage;
        
        \\ Updated limit to length + 1 to check the final character
        length += 1;
        phase kai i = 1, length, 1 cos
            blaze c = uname[i];
            
            sol c >= 'A' && c <= 'Z'
                hasUpper = iris;
            mos
            soluna c >= 'a' && c <= 'z'
                hasLower = iris;
            mos
            soluna c >= '0' && c <= '9'
                hasNum = iris;
            mos
            luna
                hasSpec = iris;
            mos
        mos
        
        sol hasUpper == iris && hasLower == iris && hasNum == iris && hasSpec == iris
            isValid = iris;
            nova("Valid username entered.");
        mos
        luna
            nova("Invalid username. You are missing:");
            
            sol hasUpper == sage
                nova("- An uppercase letter");
            mos
            
            sol hasLower == sage
                nova("- A lowercase letter");
            mos
            
            sol hasNum == sage
                nova("- A number");
            mos
            
            sol hasSpec == sage
                nova("- A special character");
            mos
        mos
    mos
mos