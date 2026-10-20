# **COS30049 Week 10 Workshop. Defending a FastAPI back end** 

Oct 11, 2026 · @ricky 

## **What these demos are for** 

Each demo is one defence from Assignment 3, written out and running, so you can see what a defence looks like in real code before you build your own. The lecture showed each risk as a risky pattern and the idea behind its fix. The demos are the other half, the fix itself. 

Every demo is a small FastAPI app of about 30 to 70 lines with one defence in it, plus a test file that proves the defence holds. 

|Demo|What it shows|Assignment 3|Level|Lecture slides|
|---|---|---|---|---|
|`demo1_hygiene.p`<br>`y`|Size limit, CORS,<br>one error format,<br>secrets from the<br>environment|2.3 Security<br>hygiene, with the<br>error format from<br>2.2|Required of every<br>group|9, 13 to 15|
|`demo2_command_i`<br>`njection.py`|Validate the<br>input, then call<br>the program<br>without a shell|2.7 Command<br>injection|Basic|27|
|`demo3_rate_limi`<br>`ting.py`|Count requests<br>per client and<br>refuse the excess<br>with 429|2.7 Missing rate<br>limiting|Basic|28|
|`demo4_safe_mode`<br>`l_loading.py`|Check the model<br>file's hash before<br>loading it|2.7 Unsafe model<br>loading|Basic|26|
|`demo5_sql_param`<br>`eterised.py`|Query the<br>database with<br>parameters, so<br>input stays data|2.7 SQL injection|Intermediate|29|



Work through every demo with the same five steps. 

1. **Read** the demo file. Its first lines explain the risk and the defence, and the important lines are commented. 

2. **Run** it with uvicorn and open its /docs page. 

3. **Try** the inputs this guide lists, and check you get the response the guide says you should. 

4. **Test** it with pytest, and read the test. It shows exactly what "the defence holds" means. 

5. **Apply** it. Answer the questions at the end of each demo about your own application. 

Keep two things in mind. 

- **A demo is the principle, not a finished defence.** In Assignment 3 a defence earns full marks only when it also stops the obvious variations of the attack. Working out which variations matter for your application is part of your work. 

- **Everything runs on your own computer.** Every input in this guide is sent to the demo running on your own machine, to check that a defence rejects it. 

## **Suggested timing** 

Two hours covers demos 1 to 4 and a plan for your own project. Demo 5 is optional, for groups that will store data in a database. 

|Time|Activity|
|---|---|
|0:00 to 0:15|Set up, then run all the tests once to check<br>everything works|
|0:15 to 0:35|Demo 1, security hygiene|
|0:35 to 0:50|Demo 2, command injection|
|0:50 to 1:05|Demo 3, rate limiting|
|1:05 to 1:20|Demo 4, safe model loading|
|1:20 to 1:35|Demo 5, SQL injection (optional)|
|1:35 to 2:00|Bring it into your own project, and talk your plan<br>through with your tutor|



## **Setting up** 

Setting up takes about ten minutes and ends with all sixteen tests passing. You need Python 3.10 or later. 

1. Download <mark>`COS30049_Week10_Demos.zip`</mark> , unzip it, and open a terminal inside the <mark>`demos`</mark> folder. Every command in this guide runs from that folder. 

2. Create a virtual environment and activate it. 

```
python -m venv .venv
source .venv/bin/activate      # macOS and Linux
.venv\Scripts\activate         # Windows
```

3. Install the packages. Their versions are pinned, which is also what section 2.4 asks of your own project. 

```
pip install -r requirements.txt
```

4. Create your <mark>`.env`</mark> file from the example. It holds settings and secrets, and it is listed in <mark>`.gitignore` ,</mark> so Git never commits it. 

```
cp .env.example .env           # macOS and Linux
copy .env.example .env         # Windows
```

5. Run the tests. You should see <mark>`16 passed` .</mark> 

#### <mark>`pytest`</mark> 

pytest may also report one warning, a deprecation notice from inside one of the libraries. It is harmless and you can ignore it. If any step fails, see Troubleshooting at the end of this guide. 

## **How to try an endpoint** 

You can send requests to a running demo in two ways, through the /docs page FastAPI builds for you, or with curl. Both send real requests to the demo on your own machine. 

Start a demo first, for example demo 1. 

```
uvicorn demo1_hygiene:app --reload --env-file .env
```

Wait until the terminal shows <mark>`Uvicorn running on http://127.0.0.1:8000` .</mark> All the demos use port 8000, so stop one with Ctrl+C before you start the next. 

### **Using the /docs page** 

1. Open http://127.0.0.1:8000/docs in your browser. 

2. Click the green bar <mark>`POST /check`</mark> to expand it. Every endpoint starts folded. 

3. Click **Try it out** , at the right end of the Parameters row. 

4. Edit the JSON under Request body. 

5. Click the blue **Execute** button, then scroll down to Server response. It shows the status code and the response body. The same panel also shows the matching curl command. 

### **Using curl** 

The curl commands in this guide are written for macOS and Linux terminals. On Windows, run them in Git Bash or WSL, or use the /docs page, because PowerShell treats quotes differently. 

**Do not paste the URL into the address bar.** A browser's address bar always sends GET, and <mark>`/check`</mark> only accepts POST, so you get <mark>`405 Method Not Allowed`</mark> . A route is a method plus a path (lecture slides 8 and 11), and the wrong method is refused. 

## **Demo 1. Security hygiene (section 2.3)** 

Demo 1 shows the back-end half of the hygiene in section 2.3, which is a size limit enforced on the back end, CORS that allows only your own front end, and secrets kept out of the code. It adds the one error format that section 2.2 asks for. The fourth hygiene requirement, never rendering user input as HTML, lives in your React front end (lecture slide 13). Every group must meet all of these, and section 2.8 earns no marks until your application meets section 2.3. 

### **Start it** 

<mark>`uvicorn demo1_hygiene:app --reload --env-file .env`</mark> **Read the code** 

- **The size limit.** <mark>`text: str = Field(min_length=1, max_length=5000)`</mark> in <mark>`CheckRequest`</mark> . Pydantic checks it before your function runs, so nobody can skip it, whatever they send. 

- **CORS.** <mark>`allow_origins=[FRONTEND_ORIGIN]`</mark> lists only your front end's exact origin. It is never <mark>`["*"]` .</mark> 

- **One error format.** The three <mark>`@app.exception_handler`</mark> functions turn every error into <mark>`{"error": ..., "detail": ...}`</mark> . That covers invalid input (422), a wrong path or method (404 and 405), and unexpected crashes (500). The 500 handler prints the real error on the server and gives the user only a generic message. 

- **Secrets from the environment.** <mark>`os.environ.get(...)`</mark> at the top reads settings that <mark>`--envfile .env`</mark> loads. No key or password is written in the code. 

**Try it** on <mark>`POST /check`</mark> in /docs. 

|Request body|Status|Response body|What it shows|
|---|---|---|---|
|`{"text": "Is this`<br>`message safe to`<br>`open?"}`|200|`{"label":"legitimat`<br>`e","confidence":0.5`<br>`}`|A normal request<br>works|
|`{"text": ""}`|422|`{"error":"invalid`<br>`input","detail":"St`<br>`ring should have at`<br>`least 1 character"}`|Empty input is refused|
|`{"text": "crash"}`|500|`{"error":"internal`<br>`error","detail":"pl`<br>`ease try again`<br>`later"}`|The user sees no<br>internal details|



After the <mark>`crash`</mark> request, look at the terminal running uvicorn. It shows <mark>`unexpected error: RuntimeError: the model service is down`</mark> , followed by the full traceback that uvicorn logs. The real error stays on the server, where you can read it, and never reaches the user. 

To see the size limit without typing 5,001 characters, change <mark>`max_length=5000`</mark> to <mark>`max_length=10`</mark> , save the file (uvicorn reloads it), and send <mark>`{"text": "longer than ten"}` .</mark> You get 422 with <mark>`String should have at most 10 characters`</mark> . Change it back afterwards. 

Now open http://127.0.0.1:8000/check in the address bar. You get 405, and the body has the same <mark>`error`</mark> and <mark>`detail`</mark> shape as every other error. 

**Check CORS with curl.** These two commands imitate the question a browser asks before a cross-origin POST, the preflight from lecture slide 14. 

```
curl -i -X OPTIONS http://127.0.0.1:8000/check -H "Origin: http://localhost:5173" -H
"Access-Control-Request-Method: POST"
curl -i -X OPTIONS http://127.0.0.1:8000/check -H "Origin: http://evil.example" -H
"Access-Control-Request-Method: POST"
```

The first answers <mark>`200 OK`</mark> with <mark>`access-control-allow-origin: http://localhost:5173` ,</mark> so a browser would let your front end read the response. The second answers <mark>`400 Bad Request`</mark> with <mark>`Disallowed CORS origin`</mark> , so a browser would refuse a page from that site. curl itself ignores CORS. Here it only asks the question a browser would ask. 

### **Run the test** 

#### <mark>`pytest tests/test_demo1.py`</mark> 

The five tests check that a normal request works, that oversized input is refused, that every error has the same shape with no internal details, that CORS answers only your front end, and that a wrong method or unknown path gets the same error shape. 

### **Questions for your own application** 

- What is the largest input your model really needs? Set the limit from that, not from a round number. 

- What is your front end's exact origin now, and what would it be once deployed? 

- Make your own back end fail. Does the response show a file path, a library name or a stack trace? 

- Search your repository for keys and passwords, including old commits. Is any secret in it? 

## **Demo 2. Command injection (section 2.7, Basic)** 

Demo 2 shows the two layers that stop command injection when your back end runs another program, such as a WHOIS lookup. 

The risk, from lecture slide 27. If the code pastes the input into a command string, as in <mark>`os.system("whois " + domain)`</mark> , a shell reads the whole string, and a `;` in the input starts a second command. Demo 2 never builds such a string. 

### **Start it** 

```
uvicorn demo2_command_injection:app --reload
```

**Read the code** 

- **Layer 1, validation.** The <mark>`DOMAIN`</mark> regular expression and the <mark>`must_look_like_a_domain`</mark> validator let through only something shaped like a domain name. The validator also trims the input and lowers its case. 

- **Layer 2, no shell.** <mark>`lookup()`</mark> calls <mark>`subprocess.run([...])`</mark> with a list. The program receives the domain as one argument, and no shell ever reads it, so a character like `;` has no special meaning. <mark>`timeout=5`</mark> stops a lookup that hangs. 

- **Why Python and not whois.** The demo runs Python as the program, so it works on every computer. In your application the list would be <mark>`["whois", domain]` .</mark> 

**Try it** on <mark>`POST /lookup`</mark> in /docs. 

|Request body|Status|Response|What it shows|
|---|---|---|---|
|`{"domain":`<br>`"example.com"}`|200|`{"domain":"example.`<br>`com","result":"look`<br>`up for`<br>`example.com"}`|A real domain is looked<br>up|
|`{"domain":`<br>`"Example.COM"}`|200|The same as above|The validator tidies the<br>input|



|Request body|Status|Response|What it shows|
|---|---|---|---|
|`{"domain":`<br>`"example.com; ls"}`|422|`Value error, not a`<br>`valid domain name`|The example from<br>section 2.7 is refused<br>before any program<br>runs|
|`{"domain": "not a`<br>`domain"}`|422|The same message|Anything that is not a<br>domain is refused|



Demo 2 keeps FastAPI's default error format to stay short, so its 422 body also repeats the input. In your application, add demo 1's error handlers as well. 

### **Run the test** 

```
pytest tests/test_demo2.py
```

The four tests check that a real domain is looked up, that the example from section 2.7 is refused, that something which is not a domain is refused, and that <mark>`lookup()`</mark> passes its argument through literally. 

### **Questions for your own application** 

- Does your back end start another program anywhere? If not, this risk does not apply, and your threat model should say so in one line. 

- What exactly counts as a valid input for that program in your application? Write the rule down before you write the regular expression. 

- Either layer alone stops the example. Why keep both? 

## **Demo 3. Rate limiting (section 2.7, Basic)** 

Demo 3 lets each client make five requests a minute and refuses the sixth with status 429. 

The risk, from lecture slide 28. FastAPI sets no limit, so one client can call your model as often as it likes. That costs you a model run every time, and unlimited queries also let someone map exactly how your model decides. 

### **Start it** 

```
uvicorn demo3_rate_limiting:app --reload
```

**Read the code** 

- **Who counts as one client.** <mark>`Limiter(key_func=get_remote_address)`</mark> counts requests per address the request comes from. 

- **The limit.** <mark>`@limiter.limit("5/minute")`</mark> on the endpoint allows five requests per client per minute. A real limit would be higher. Five is simply easy to see in a demo. 

- **The extra parameter.** The endpoint takes <mark>`request: Request`</mark> because slowapi needs it to see who is calling. 

- **The 429 response.** <mark>`app.add_exception_handler(RateLimitExceeded, ...)`</mark> turns the excess into a 429 Too Many Requests response. 

**Try it** on <mark>`POST /check`</mark> in /docs. Send <mark>`{"text": "hello"}`</mark> and click Execute six times in a row. 

|Request|Status|Response|
|---|---|---|
|1st to 5th|200|`{"label":"legitimate","con`<br>`fidence":0.5}`|
|6th|429|`{"error":"Rate limit`<br>`exceeded: 5 per 1 minute"}`|



Wait a minute and requests work again. Restarting the server also resets the count, because the demo keeps its counts in memory. 

### **Run the test** 

```
pytest tests/test_demo3.py
```

The two tests check that five requests inside the limit succeed and that the sixth gets 429. <mark>`limiter.reset()`</mark> clears the count before each test, so the tests do not affect each other. 

### **Questions for your own application** 

- How many checks would a real person make in a minute? Choose a limit they never reach. 

- What identifies one client in your deployment, and could a client change it? 

- The counts live in memory, so a restart clears them and two servers would not share them. Does that matter for your application? 

- If you choose both rate limiting and denial of service, section 2.7 asks that each relies on a different mechanism. What would yours be? 

## **Demo 4. Safe model loading (section 2.7, Basic)** 

Demo 4 checks the model file's SHA-256 hash before loading it, and refuses to start if the file has changed. 

The risk, from lecture slide 26. <mark>`joblib.load`</mark> and <mark>`pickle.load`</mark> can run code hidden inside the file, so a tampered model file runs that code the moment the server loads it. Almost every group loads its model this way. 

**Start it** in three steps. 

1. Create the model file and its hash. 

```
python make_model.py
```

This writes <mark>`model.joblib` ,</mark> a tiny stand-in for your Assignment 2 model so the demo needs no scikitlearn, and prints a line <mark>`MODEL_SHA256=`</mark> followed by a 64-character hash. 

2. Copy that whole line into <mark>`.env` ,</mark> replacing the empty <mark>`MODEL_SHA256=`</mark> line. 

3. Start the server. 

```
uvicorn demo4_safe_model_loading:app --reload --env-file .env
```

**Read the code** 

- **<mark>`sha256_of()`</mark>** reads the file in chunks and returns its SHA-256 hash. Changing even one byte of the file gives a completely different hash. 

- **<mark>`load_model()`</mark>** refuses to load in two cases, when no hash was recorded and when the hashes differ. Only after both checks does it call <mark>`joblib.load` .</mark> 

- **<mark>`lifespan`</mark>** runs <mark>`load_model()`</mark> once, when the server starts. That is also what section 2.2 asks, the model loaded once and not on every request. If the check fails, the server never starts. 

### **Try it** 

|What you do|What happens|
|---|---|
|Start with the right hash in `.env`,then send|The server starts and answers 200 with|
|`{"text": "hello"}` to`POST /check`|`{"label":"legitimate","confidence":0.5}`|
|Stop the server, change the first character of the<br>hash in `.env`,and start it again|The server refuses to start. The terminal shows<br>`model file hash does not match the`<br>`recorded hash, refusing to load`,then<br>`Application startup failed`|
|Stop the server, leave `MODEL_SHA256=`empty,<br>and start it again|The server refuses to start, with`MODEL_SHA256`<br>`is not set, refusing to load an`<br>`unverified model`|



Changing the hash stands in for changing the file. Either way the two no longer match, and the file is never loaded. Put the right hash back when you finish. 

### **Run the test** 

```
pytest tests/test_demo4.py
```

The three tests check that a file with the recorded hash loads, that a copy with one byte changed is refused, and that no recorded hash means no load. The one-byte change is exactly what a tampered file looks like to the hash. 

### **Questions for your own application** 

- When will you compute the hash of your real model? Doing it as part of saving the model means it is never forgotten. 

- Where should the recorded hash live, so that someone who can replace the model file cannot also replace the hash? 

- How will you show the server refusing a changed model in your video? 

## **Demo 5. SQL injection (section 2.7, Intermediate, optional)** 

Demo 5 stores a history of checks in SQLite and queries it only through parameters, so input always stays data. 

The risk, from lecture slide 29. Building a query by pasting the input into the SQL text lets input such as `'` <mark>`OR '1'='1`</mark> become part of the SQL itself. It sits at Intermediate because you first need a database feature, such as a history of past checks. 

### **Start it** 

```
uvicorn demo5_sql_parameterised:app --reload
```

On its first start it creates <mark>`history.db`</mark> in the folder. Delete that file whenever you want an empty history again. 

### **Read the code** 

- **<mark>`lifespan`</mark>** creates the <mark>`checks`</mark> table once, when the server starts. 

- **<mark>`get_db()`</mark>** opens a database connection for each request and closes it afterwards. FastAPI passes it in through <mark>`Depends`</mark> . 

- **<mark>`add_check()`</mark>** runs <mark>`INSERT INTO checks (text, label) VALUES (?, ?)`</mark> and passes the values separately as <mark>`(req.text, label)` .</mark> Each `?` is a placeholder. The database receives the SQL and the values apart, so a value can never change the SQL. 

- **<mark>`search()`</mark>** does the same with <mark>`LIKE ?` .</mark> Even the `%` wildcards are added to the value, never to the SQL text. 

- An ORM such as SQLAlchemy builds parameterised queries for you in the same way. 

**Try it** in /docs, starting from an empty history. 

|Step|Request|Response|What it shows|
|---|---|---|---|
|1|`POST /history`with<br>`{"text": "hello`<br>`world"}`|`{"id":1,"text":"hel`<br>`lo`<br>`world","label":"leg`<br>`itimate"}`|A normal check is<br>stored|
|2|`POST /history`with<br>`{"text": "' OR`<br>`'1'='1"}`|`{"id":2,"text":"'`<br>`OR`<br>`'1'='1","label":"le`<br>`gitimate"}`|The example from<br>section 2.7 is stored<br>exactly as typed|
|3|`GET`<br>`/history/search`,<br>type`hello` in the`q`box|Only the`hello world`<br>row|The query still means<br>what it says|
|4|The same, with `OR '1'`<br>in the`q`box|Only the row from step<br>2|The example is found<br>as text, nothing more|
|5|The same, with `zzz`in<br>the`q`box|`[]`|No match, no rows|



With string pasting, as on lecture slide 29, the input in step 2 would become part of the SQL. With parameters it is only ever data. 

### **Run the test** 

```
pytest tests/test_demo5.py
```

The two tests check that the example input is stored and returned unchanged, and that searches return only the rows that really match. Each test uses its own temporary database, so your <mark>`history.db`</mark> is not touched. 

### **Questions for your own application** 

- Does your application need a database at all? If it stores nothing, this risk does not apply, and your threat model should say so in one line. 

- List every query your back end runs. Does each one use parameters or an ORM? 

- Some parts of a query, such as a column to sort by, cannot be parameters. How would you handle one of those safely? 

## **Bring it into your own project** 

Use the last 25 minutes to turn the demos into a plan for your own back end, then talk it through with your tutor. 

A demo shows the principle on a toy app. In your application the same defence has to fit your real inputs, your real model and your real routes, and it has to hold against the variations your threat model points to. The rubric marks that, not the demo. 

The demos cover the Basic and Intermediate defences most groups start with. Full marks in section 2.7 also need an Advanced defence, which lecture slides 32 to 35 introduce. 

Work through this checklist as a group. 

- ☐ Our application meets all four hygiene requirements of section 2.3, and every error uses one JSON format (section 2.2). 

- ☐ Our threat model answers the three questions for our own design (lecture slides 18 to 22). 

- ☐ We know which of the nine risks our design has, and why the others do not apply. 

- ☐ We have chosen up to two defences and named them in our README. 

- ☐ For each defence, we have listed the obvious variations it must also stop. 

- ☐ For each defence, we have planned how our video shows the attack succeeding without it and failing with it (lecture slide 38). 

- ☐ For each defence, we have written a test in the style of the demo tests. 

## **Troubleshooting and glossary** 

Most problems come from the terminal being in the wrong folder or the virtual environment not being active. 

|What you see|Why|What to do|
|---|---|---|
|`uvicorn: command not found`|The virtual environment is not|Activate`.venv`, then run`pip`|
|or`pytest: command not`<br>`found`|active, or the packages are not<br>installed|`install -r`<br>`requirements.txt`|
|`No module named`<br>`'demo1_hygiene'`|The terminal is not in the`demos`<br>folder|Move into the `demos` folder and<br>run the command again|
|`address already in use`|Another demo is still running on<br>port 8000|Stop it with Ctrl+C, or add`--`<br>`port 8001` to the command|
|`Invalid value for '--env-`<br>`file': Path '.env' does`|There is no `.env` file yet|Copy `.env.example`to`.env`|



|What you see|Why|What to do|
|---|---|---|
|`not exist`||(Setting up, step 4)|
|You cannot see`.env.example`<br>or`.env` in Finder|macOS hides names that start<br>with a dot|Press Cmd+Shift+. in Finder, or<br>open the folder in VS Code|
|The /docs page is blank|The page loads its scripts from<br>cdn.jsdelivr.net, and your<br>network blocks it|Try another network, or use curl|
|`405` or`Method Not Allowed`|You opened a POST endpoint in<br>the address bar|Use /docs or curl|
|Demo 4 will not start|The hash in`.env` is missing or<br>wrong, which is the defence<br>working|Run`python make_model.py`<br>and copy its line into`.env`|
|Demo 4 says`MODEL_SHA256 is`<br>`not set` although`.env` has the<br>hash|It was started without `--env-`<br>`file .env`|Start it with the full command<br>from Demo 4|
|Demo 3 answers 429 straight<br>away|Earlier requests still count for<br>this minute|Wait a minute, or restart the<br>server|
|Demo 5 ids are higher than in<br>the table|`history.db` remembers earlier<br>runs|Delete`history.db`and restart|
|`python` is not found|macOS often names it`python3`,<br>and Windows`py`|Use`python3` or`py`to create the<br>virtual environment. Once it is<br>active,`python` works on every<br>system|
|PowerShell refuses to run the<br>activate script|Its execution policy blocks<br>scripts|Run`Set-ExecutionPolicy -`<br>`Scope CurrentUser -`<br>`ExecutionPolicy`<br>`RemoteSigned`once, or use<br>Command Prompt|
|curl on Windows rejects the|PowerShell and Command|Use Git Bash, WSL or the /docs|
|JSON or the quotes|Prompt treat quotes differently|page|



|**Glossary**||
|---|---|
|Term|Meaning|
|Route|A method plus a path that runs one function,|
||such as`POST /check`|
|Status code|The number that says how a request went, such|



|Term|Meaning|
|---|---|
||as 200, 422 or 429|
|Pydantic model|A class that describes the shape and limits of a<br>request body. FastAPI checks every request<br>against it|
|Exception handler|A function that turns an error into the response<br>the user sees|
|Middleware|Code that runs around every request, such as<br>`CORSMiddleware`|
|Origin|The scheme, host and port together, such as<br>`http://localhost:5173`|
|SHA-256 hash|A 64-character fingerprint of a file. Any change to<br>the file gives a different one|
|Parameterised query|SQL sent with`?`placeholders, with the values<br>sent separately|
|Virtual environment|A private folder of packages for one project|
|`.env` file|A file of settings and secrets loaded into the<br>environment and never committed|



## **Ethics** 

**All security testing in this assignment is limited to your own application, running on your own machine. Never test any system you do not own, including another group's application.** 

Everything in this guide follows that rule. Each demo runs on your own computer at 127.0.0.1, and the tests run inside pytest without touching the network at all. Work the same way in Assignment 3. Record the "without the defence" part of your video against your own copy, running locally, and ask your tutor first if you are unsure whether something is allowed. 

