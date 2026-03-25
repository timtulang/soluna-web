nova("=== Problem 2: Duplicate/Triplicate Checker ===");
hubble kai history = {};
kai count = 0;
lani stopLoop = sage;

orbit stopLoop == sage cos
    nova("Enter a number:");
    kai current = lumina();
    
    kai occurrences = 0;
    phase kai i = 0, count, 1 cos
        sol history[i] == current
            occurrences += 1;
        mos
    mos
    
    sol occurrences == 1
        nova("Duplicate found: " .. current);
    mos
    soluna occurrences == 2
        nova("Triplicate found! Stopping.");
        stopLoop = iris;
    mos
    
    history[count] = current;
    count += 1;
mos