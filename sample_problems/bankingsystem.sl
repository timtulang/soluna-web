nova("=== Banking Transactions System ===");

hubble selene names = {"", "", "", "", "", ""};
hubble kai accounts = {0, 0, 0, 0, 0, 0};
hubble kai balances = {0, 0, 0, 0, 0, 0};
hubble kai initBal = {0, 0, 0, 0, 0, 0};
hubble kai dailyDep = {0, 0, 0, 0, 0, 0};
hubble kai dailyWit = {0, 0, 0, 0, 0, 0};
hubble kai dailyCount = {0, 0, 0, 0, 0, 0};
hubble kai totalTransaction = {0, 0, 0, 0, 0, 0};
hubble selene lastDate = {"", "", "", "", "", ""};
hubble selene dateHistory = {"empty", "empty", "empty", "empty", "empty", "empty", "empty", "empty", "empty", "empty", "empty", "empty", "empty", "empty", "empty", "empty", "empty", "empty", "empty", "empty", "empty", "empty", "empty", "empty", "empty", "empty"};

lani validNC = sage;
kai nClients = 0;
orbit validNC == sage cos
    lumen("Enter number of clients (1-5): ");
    nClients = lumina();
    sol nClients >= 1 and nClients <= 5
        validNC = iris;
    mos
    luna
        nova("Error: Number of clients must be between 1 and 5.");
    mos
mos

lani validMT = sage;
kai maxTransaction = 0;
orbit validMT == sage cos
    lumen("Enter max transaction per day (1-5): ");
    maxTransaction = lumina();
    sol maxTransaction >= 1 and maxTransaction <= 5
        validMT = iris;
    mos
    luna
        nova("Error: Max transaction must be between 1 and 5.");
    mos
mos

kai limit = nClients + 1;

phase kai i = 1, limit, 1 cos
    nova("\nSetup Client " .. i);
    lumen("Name: "); names[i] = lumina();
    lani validAcc = sage;
    orbit validAcc == sage cos
        lumen("Account Number: ");
        kai tempAcc = lumina();
        sol tempAcc <= 0
            nova("Error: Account number must be positive.");
        mos
        luna
            lani isDup = sage;
            phase kai j = 1, i, 1 cos
                sol accounts[j] == tempAcc isDup = iris; 
                mos
            mos
            sol isDup == iris
                nova("Error: Account number already exists.");
            mos
            luna
                accounts[i] = tempAcc;
                validAcc = iris;
            mos
        mos
    mos
    lani validBal = sage;
    orbit validBal == sage cos
        lumen("Initial Balance: ");
        kai inBal = lumina();
        sol inBal >= 0
            balances[i] = inBal;
            initBal[i] = inBal;
            validBal = iris;
        mos
        luna nova("Error: Balance cannot be negative."); 
        mos
    mos
mos

lani running = iris;
orbit running == iris cos
    nova("\n--- BANK MENU ---");
    nova("1. Deposit");
    nova("2. Withdraw");
    nova("3. Balance Inquiry");
    nova("4. Transaction Summary");
    nova("5. Exit");
    
    kai choice = 0;
    lani validChoice = sage;
    orbit validChoice == sage cos
        lumen("Choice (1-5): ");
        choice = lumina();
        sol choice >= 1 and choice <= 5
            validChoice = iris;
        mos
        luna
            nova("Error: Invalid Choice! Select between 1 and 5.");
        mos
    mos

    sol choice == 5
        running = sage;
    mos
    luna
        nova("\nSelect Client:");
        phase kai i = 1, limit, 1 cos
            nova(i .. ". " .. names[i]);
        mos
        lumen("Enter Index: ");
        kai idx = lumina();

        sol idx > 0 and idx <= nClients
            sol choice == 1 or choice == 2
                lani dateOk = sage;
                selene dInput = "";
                orbit dateOk == sage cos
                    lumen("Enter Date (MM/DD/YYYY): ");
                    dInput = lumina();
                    lani hasLetter = sage;
                    phase kai k = 1, 11, 1 cos
                        blaze c = dInput[k];
                        sol (c >= 'a' and c <= 'z') or (c >= 'A' and c <= 'Z')
                            hasLetter = iris;
                        mos
                    mos
                    sol hasLetter == iris
                        nova("Error: Letters are not allowed in date.");
                    mos
                    luna dateOk = iris; mos
                mos

                sol dInput != lastDate[idx]
                    dailyCount[idx] = 0;
                    dailyDep[idx] = 0;
                    dailyWit[idx] = 0;
                    lastDate[idx] = dInput;
                    
                    kai historyIdx = ((idx - 1) * 5) + 1;
                    lani added = sage;
                    phase kai h = 0, 5, 1 cos
                        selene currentStored = dateHistory[historyIdx + h];
                        sol currentStored == "empty" and added == sage
                            dateHistory[historyIdx + h] = dInput;
                            added = iris;
                        mos
                    mos
                mos

                sol dailyCount[idx] < maxTransaction
                    sol choice == 1
                        lumen("Deposit Amount: ");
                        kai dep = lumina();
                        sol dep > 0 and (dailyDep[idx] + dep) <= 50000
                            balances[idx] = balances[idx] + dep;
                            dailyDep[idx] = dailyDep[idx] + dep;
                            dailyCount[idx] = dailyCount[idx] + 1;
                            totalTransaction[idx] = totalTransaction[idx] + 1;
                            nova("Deposit Success!");
                        mos
                        luna nova("Error: Invalid amount or Daily Limit (50k) reached!"); 
                        mos
                    mos

                    soluna choice == 2
                        lumen("Withdraw Amount: ");
                        kai wit = lumina();
                        sol wit > 0 and wit <= balances[idx] and (dailyWit[idx] + wit) <= 20000
                            balances[idx] = balances[idx] - wit;
                            dailyWit[idx] = dailyWit[idx] + wit;
                            dailyCount[idx] = dailyCount[idx] + 1;
                            totalTransaction[idx] = totalTransaction[idx] + 1;
                            nova("Withdraw Success!");
                        mos
                        luna nova("Error: Invalid amount, Insufficient balance, or Daily Limit (20k) reached!"); 
                        mos
                    mos
                mos
                luna nova("Error: Max daily transaction reached for " .. dInput); 
                mos
            mos

            soluna choice == 3
                nova("\nAccount: " .. accounts[idx]);
                nova("Name: " .. names[idx]);
                nova("Current Balance: " .. balances[idx] .. " PHP");
            mos

            soluna choice == 4
                nova("\n--- TRANSACTION SUMMARY OPTION ---");
                nova("1. Overall Summary");
                nova("2. Specific Date Summary");
                lumen("Selection: "); kai sumChoice = lumina();

                sol sumChoice == 1
                    nova("\n--- OVERALL SUMMARY ---");
                    nova("Client: " .. names[idx]);
                    nova("Account: " .. accounts[idx]);
                    nova("Overall Total Transactions: " .. totalTransaction[idx]);
                    nova("Final Balance: " .. balances[idx]);
                mos
                soluna sumChoice == 2
                    sol totalTransaction[idx] == 0
                        nova("\nNo transactions have occurred yet for this client.");
                        nova("Initial Balance: " .. initBal[idx] .. " PHP");
                    mos
                    luna
                        nova("\nInputted Dates History for " .. names[idx] .. ":");
                        kai historyIdx = ((idx - 1) * 5) + 1;
                        phase kai h = 0, 5, 1 cos
                            selene historyDate = dateHistory[historyIdx + h];
                            sol historyDate != "empty"
                                nova("- " .. historyDate);
                            mos
                        mos
                        
                        lumen("\nEnter Date from list (MM/DD/YYYY): ");
                        selene sDate = lumina();
                        nova("\n--- DATE SUMMARY ---");
                        sol sDate == lastDate[idx]
                            nova("Date: " .. sDate);
                            nova("Transactions on this date: " .. dailyCount[idx]);
                        mos
                        luna
                            nova("Note: Detailed count only available for active date.");
                        mos
                        nova("Current Balance: " .. balances[idx]);
                    mos
                mos
            mos
        mos
        luna 
            nova("Invalid Index!");
        mos
    mos

    sol running == iris
        lumen("\nContinue? (Y/N): ");
        blaze cont = lumina();
        sol cont == 'N' or cont == 'n' running = sage; 
        mos
    mos
mos
nova("System Terminated.");