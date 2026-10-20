

<!-- Start of picture text -->
SWI N SWINBURNE<br>B1} R UNIVERSITY OF<br>~NE« TECHNOLOGY<br><!-- End of picture text -->

**Week 10** 

## **The back end, and how it gets attacked** 

FastAPI in brief, threat modelling, and the nine risks in Assignment 3 

Presented by Ricky Dong COS30049 Computing Technology Innovation Project Semester 2, 2026 

### **Acknowledgement of Country** 

We respectfully acknowledge the Wurundjeri People of the Kulin Nation, who are the Traditional Owners of the land on which Swinburne's Australian campuses are located in Melbourne's east and outer-east, and pay our respect to their Elders past, present and emerging. 



|**Objectives**|
|---|
|**1.  Explain what a FastAPI back end does in your application, and why security has to live there**|
|**2.  Write a threat model that answers three questions about your own application**|
|**3.  Recognise the nine risks in section 2.7, where each one sits, and the idea behind each fix**|
|**4.  Choose two defences that fit your threat model, and know how they are marked**|
|Today is about what each risk is. Next week covers advanced security, and how to prove a defence works with numbers.|





### **This week and next** 

The same application, now facing input that is meant to break it. 

**Earlier weeks This week Next week React front end Back end and security Advanced security** forms, state, and the charts that show a FastAPI, threat models, and the nine side channels, attacks on the model, result risks in section 2.7 and measuring a defence 

Every topic in this unit is a cybersecurity problem, so your application will receive hostile input by design. Making it secure is the focus of Assignment 3, and the main route to the highest marks. 



Part 1 

#### **The back end, briefly** 

What it does in your application, and why security has to live there. 



<!-- Start of picture text -->
SWi N SWINBURNE<br>B U R UNIVERSITY OF<br>aN TECHNOLOGY<br><!-- End of picture text -->



### **What the back end does in your application** 

Your front end never touches the model. It sends a request, and the back end does the work. 



<!-- Start of picture text -->
Model<br>request (JSON) loaded once, at start-up<br>Browser FastAPI back end<br>React front end 1   checks the request<br>the form, the result 2   runs the model<br>and the charts 3   returns the result as JSON<br>response (JSON) Database<br>only if you store data<br><!-- End of picture text -->

In Assignment 3 the back end is FastAPI. It checks every request, runs your model, and returns the result as JSON. The model is loaded once, when the server starts, not on every request. 

**Everything goes through the back end. So does every attack in this lecture.** 



### **An HTTP request, piece by piece** 

Every attack in this lecture is, in the end, a carefully chosen request. 

```
POST /check HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Origin: http://localhost:5173
{"text": "Is this message safe to open?"}
```

###### **Request line** 

The method, POST, and the path, /check. Together they pick which code runs. 

###### **Headers** 

Extra information, such as the type of the body and the page that sent it. **Body** The data itself, here as JSON. For an upload, the file. 

Whoever sends a request chooses every part of it. The method, the path, every header and the whole body are all input, and none of it can be trusted. 



<!-- Start of picture text -->
BUR Sissies<br>»NE#<br><!-- End of picture text -->

### **HTTP methods, and what each one is for** 

|The method says wh<br>|at the client wants done. The path says what to<br>|do it to.<br>||
|---|---|---|---|
|**Method**|**Use it to**|**Example**|**Body**|
|**`GET`**|read something, without changing anything|`GET /history`|none, details go in the URL|
|**`POST`**|send data to be processed or stored|`POST /check`|JSON|
|**`PUT, PATCH`**|replace or update something that exists|`PATCH /history/42`|JSON|
|**`DELETE`**|remove something|`DELETE /history/42`|usually none|



**In FastAPI, the decorator picks the method** @app.get, @app.post, @app.put, @app.patch and @app.delete. Section 2.2 asks for at least two methods, each used for a genuine purpose. 

##### **The wrong method gets 405** 

The browser's address bar always sends GET. Open a POST-only endpoint there and FastAPI answers 405 Method Not Allowed. 



### **The response, and what status codes mean** 

The status code says what happened before the client reads a single byte of the body. 

|`HTTP/1.1 200 OK`|**`200`**|The request worked|
|---|---|---|
|`Content-Type: application/json`|||
|`{"label": "phishing",`|**`422`**|The input failed validation, FastAPI's default|
|`"confidence": 0.93}`|**`404`**|Nothing exists at that path|
||**`429`**|Too many requests, as in rate limiting|
||**`500`**|Something broke inside the server|
||**`503`**|The server is refusing extra work for now|



Section 2.2 asks for correct status codes, and one consistent JSON format for every error, without stack traces or other internal details. 



<!-- Start of picture text -->
BUR Sissies<br>»NE#<br><!-- End of picture text -->

### **A FastAPI endpoint, in a dozen lines** 

The seminar goes through FastAPI hands-on. Here is the shape of it. 

```
from fastapiimport FastAPI
from pydanticimport BaseModel, Field
app = FastAPI()
class CheckRequest(BaseModel):
text: str = Field(min_length=1, max_length=5000)
class CheckResult(BaseModel):
label: str
confidence: float
@app.post("/check", response_model=CheckResult)
def check(req: CheckRequest):
label, confidence = classify(req.text)  # your model
return CheckResult(label=label, confidence=confidence)
```

##### **Pydantic checks the body** 

Input that does not match the model is rejected with 422, before your code runs. 

##### **The decorator sets the route** 

A POST to /check runs this function. 

##### **Documentation for free** 

FastAPI builds interactive docs at /docs from this code. 



<!-- Start of picture text -->
BUR gages<br>»NE#<br><!-- End of picture text -->

### **One path, several routes** 

A route is a method plus a path. The same path can do very different things. 

```
GET     /history        list my past checks
GET     /history/42     read check 42
DELETE  /history/42     delete check 42
```

##### **Each route is separate code** 

A check that is missing from one route is a hole, even when the others are safe. 

##### **Notice the 42** 

It sits in the path, so anyone can change it to 43. Remember this when we reach broken access control. 



<!-- Start of picture text -->
BUR | Yesens<br>*NE*<br><!-- End of picture text -->

### **Attackers do not use your front end** 

Front-end checks are for usability. Back-end checks are for security. 

##### **What a user does** 

Types into your React form. Your checks run, and the request that arrives looks well formed. 

##### **What an attacker does** 

Skips your form and sends a raw request with curl or Postman. Your front-end checks never run. 

```
curl -X POST http://localhost:8000/check \
```

```
-H "Content-Type: application/json" \
```

```
-d '{"text": "anything at all, of any length"}'
```

If a check matters for security, it has to run on the back end. Sending requests directly is also how you will demonstrate most of your defences. 



<!-- Start of picture text -->
BUR | Yesens<br>*NE*<br><!-- End of picture text -->

### **The minimum every application needs** 

Section 2.3. Required of every group, and needed before section 2.8 can earn any marks. 

##### **Never render input as HTML** 

React escapes text for you. Never bypass it, for example with dangerouslySetInnerHTML. 

##### **CORS allows only your front end** 

List your front end's exact origin, never every origin. 

##### **Limit size on the back end** 

Text inputs and file uploads both, enforced where an attacker cannot step around it. 

##### **Keep secrets out of the code** 

Keys and passwords live in environment variables, not in the repository. 

None of these takes much work. An application that misses them cannot reach the higher grades. 



<!-- Start of picture text -->
BUR | Yesens<br>*NE*<br><!-- End of picture text -->

### **What CORS is** 

A browser rule that protects users. Your back end only tells the browser who may read its responses. 

###### **An origin is the scheme, the host and the port** 

**An origin is the scheme, the host and the port** `app.add_middleware( CORSMiddleware,` **this page calls this API** `allow_origins=["http://localhost:5173"], allow_methods=["POST"], http://localhost:5173 http://127.0.0.1:8000` **different host and port** `allow_headers=["Content-Type"], ) http://localhost:5173 http://localhost:8000` **different port** `http://127.0.0.1:8000 http://127.0.0.1:8000` **same origin** Section 2.3. Your front end's exact origin, never every origin. **The same-origin policy CORS** By default, JavaScript on one origin cannot read a response from The server names, in the Access-Control-Allow-Origin header, another origin. The browser enforces this. which other origins may read its responses. In FastAPI, CORSMiddleware sets it. **It protects users, not your server** curl, Postman, scripts and other servers ignore CORS completely. It never replaces authentication, rate limiting or input validation. 

For a JSON POST the browser first asks with an OPTIONS request, called a preflight. CORSMiddleware answers it for you. 



<!-- Start of picture text -->
BUR | Yesens<br>*NE*<br><!-- End of picture text -->

### **Why the rule exists, the bank example** 

You are logged in to your bank in one tab, and open a malicious site in another. 

```
// a script on https://evil.com
fetch("https://bank.com/api/balance",
```

```
{ credentials: "include" })
```

```
.then(r => r.json())
```

```
.then(data => { /* send it to evil.com */ })
```

##### **How the bank uses CORS** 

Its own front ends need to read its API, so the API names exactly those origins, for example Access-Control-Allow-Origin: https://bank.com. A page from evil.com is not on the list, so the browser will not let it read. 

- **1** You open evil.com while still logged in to your bank. 

##### **The mistake to avoid** 

- **2** Its script sends a request to bank.com. 

Allowing every origin, or echoing back whatever origin asks. Then any site's script can read what the API returns. 

- **3** The browser attaches your bank.com cookie. 

- **4** The bank sees a logged-in user and returns your balance. 

- **5 The script reads the balance and sends it to evil.com.** 

##### **What it does not stop** 

The request can still reach the bank. CORS only decides whether the page may read the answer. 

- **The same-origin policy blocks this step.** 



Part 2 

#### **Threat modelling** 

Decide what you are defending against before you defend it. 



<!-- Start of picture text -->
SWi N SWINBURNE<br>B U R UNIVERSITY OF<br>aN TECHNOLOGY<br><!-- End of picture text -->



### **What a threat model is** 

A short, structured answer to what could go wrong, written before it does. 

- **1** What are we working on? **2** What can go wrong? **3** What are we going to do about it? 

**How it maps to Assignment 3** Assignment 3 asks you to answer the second question carefully, for your own application. Your defences answer the third. The evidence in your video answers the fourth. 

- **4** Did we do a good job? 

Shostack's Four Question Framework 



### **The three questions in Assignment 3** 

Half a page in your README, summarised in your video before you show your defences. 

1.  Who would want to attack your application? 2.  What are they trying to achieve? 3.  What can they actually do to it? 

##### **Why it matters** 

Your answers justify your choices in section 2.7. They also show which risks your design does not have. An application with no database cannot suffer SQL injection, and saying so briefly is part of a good threat model. 



<!-- Start of picture text -->
BUR | Yesens<br>*NE*<br><!-- End of picture text -->

### **Two ways to attack a detector** 

Your application is a detector. An attacker can go after the model, or after everything around it. 

##### **Fool the model** 

Craft input the model gets wrong, so a phishing link is judged legitimate or an injection slips past the guardrail. Look-alike Unicode characters are one example. This is section 2.8, next week. 

##### **Attack the application** 

Ignore the model's answer and go after the service itself. Overload it, make it run a command, make it reach an internal address, or read another user's data. This is section 2.7, today. 

A good threat model considers both. The same person who wants their link to pass may also try to break the service that checks it. 



<!-- Start of picture text -->
BUR | Yesens<br>*NE*<br><!-- End of picture text -->

### **Each topic has a natural attacker** 

A starting point for your threat model, not the only answer. 

|**Phishing URL detection**|A phisher who wants their link to pass as legitimate|
|---|---|
|**Prompt injection guardrail**|An attacker who wants an injection to get past the guardrail|
|**AI-generated content detection**|Someone who wants AI-generated content judged human-made|
|**Log anomaly detection**|An intruder hiding their activity among normal logs, with log lines that may themselves<br>carry malicious content|
|Whoever you name, they reach your back|end directly, not through your interface.|





### **A worked example, phishing URL detection** 

One possible design. It takes a URL, looks up its domain with WHOIS, scores it, and stores nothing. 

##### **Who** 

A phisher. 

##### **Wants** 

###### **Risks this design has** 

Command injection, because WHOIS runs as a system command. SSRF, because the back end makes a request based on the input. Rate limiting and denial of service. Misconfiguration. Unsafe model loading if the model is a joblib file. 

Their link judged legitimate, or the checker made useless. 

##### **Can do** 

Send any URL, as often as they like, straight to the back end. Through the WHOIS lookup, they choose what the server looks up. 

###### **Risks it does not have, and why** 

SQL injection, with no database. Broken access control, with no accounts. Unsafe file upload, with no files accepted. 

Only now choose two defences, from the first list, and use the threat model to explain why those two matter most for this design. 



<!-- Start of picture text -->
BUR | Yesens<br>*NE*<br><!-- End of picture text -->

### **A generic threat model, and a specific one** 

The rubric rewards the second kind. 

##### **Generic** 

"Hackers might attack our website with SQL injection, XSS, DDoS and malware."  This could describe any application, and it names attacks the design may not even have. 

##### **Specific** 

"A phisher wants their URL judged legitimate. They can send any URL directly. Our back end runs WHOIS on the domain they choose, so command injection and SSRF apply. We store nothing and have no accounts, so SQL injection and access control do not." 

##### **What a strong threat model does** 

Specific to your application, naming the risks your design exposes, and saying briefly why the others do not apply. 



<!-- Start of picture text -->
BUR | Yesens<br>*NE*<br><!-- End of picture text -->

Part 3 

#### **Nine risks, three levels** 

Section 2.7. Choose up to two defences, worth up to 7 marks together. 



<!-- Start of picture text -->
SWi N SWINBURNE<br>B U R UNIVERSITY OF<br>aN TECHNOLOGY<br><!-- End of picture text -->



### **Where the nine risks sit** 

Each one sits where a request, a file or a lookup crosses into or out of your back end. 



<!-- Start of picture text -->
Unsafe model loading<br>FastAPI back end<br>Model file<br>loaded at start-up<br>checks each request<br>Rate limiting<br>runs the model<br>returns JSON<br>Unsafe file upload<br>SQL injection<br>Anyone Database<br>a browser, or curl if you store data<br>Broken access control<br>Denial of service<br>Command injection<br>Outside world<br>Misconfiguration and vulnerable<br>WHOIS, web pages<br>dependencies<br>SSRF<br>Basic, up to 2 Intermediate, up to 3 Advanced, up to 4 Dashed boxes exist only in some designs.<br><!-- End of picture text -->



### **Three levels, by how much work a defence takes** 

The level caps the marks. It reflects the effort to build and demonstrate, not how dangerous the risk is. 

- **Basic Intermediate Advanced** up to 2 marks each up to 3 marks each up to 4 marks each •  Unsafe model loading •  SQL injection •  Denial of service •  Command injection •  Unsafe file upload •  Server-side request forgery (SSRF) •  Missing rate limiting •  Misconfiguration and vulnerable •  Broken access control dependencies 

Choose up to two. Their marks are added and capped at 7, so full marks need one Advanced defence together with an Intermediate or Advanced one. 



**BASIC** up to 2 marks 

### **Unsafe model loading** 

Whenever you load a model with joblib or pickle, which you probably already do. 

```
import joblib
```

```
# joblib.load unpickles the file, and
# unpickling can run code hidden inside it
model = joblib.load("model.joblib")
```

###### **The attack** 

A tampered model file, from a download script, a shared drive or someone else's repository. Its hidden code runs the moment the server loads it. 

##### **The fix, in principle** 

Record the file's SHA-256 hash when you train the model. Each time the server starts, hash the file again and refuse to load it if the two do not match. 

###### **In the wild** 

In February 2024 JFrog reported around 100 malicious models on Hugging Face. Loading one PyTorch model ran a hidden pickle payload that opened a reverse shell to a remote server. Python's own documentation warns that the pickle module is not secure. 

JFrog (2024). Python Software Foundation, pickle documentation. joblib documentation, joblib.load. 



<!-- Start of picture text -->
BUR gages<br>*NE*<br><!-- End of picture text -->

**BASIC** up to 2 marks 

### **Command injection** 

Whenever your back end runs a system command, such as the whois tool. 

```
import os
```

```
# the input becomes part of a shell command
os.system("whois" + domain)
```

**The attack** 

```
example.com; ls
```

The shell runs whois, then runs ls as well, a command the attacker chose. 

##### **The fix, in principle** 

Validate the input, then pass it as a list of arguments that never goes through a shell, as in subprocess.run(["whois", domain]). With no shell, there is nothing to inject into. 

###### **Read more** 

OS command injection lets an attacker run operating system commands on your server. PortSwigger's Web Security Academy and OWASP both explain it with worked examples, worth reading before you add any lookup feature. 

PortSwigger Web Security Academy, OS command injection. OWASP, Command Injection. 



<!-- Start of picture text -->
BUR gages<br>*NE*<br><!-- End of picture text -->

**BASIC** up to 2 marks 

### **Missing rate limiting** 

Every application. FastAPI sets no limit, so anyone can flood your API or probe how your model decides. 

```
@app.post("/check")
def check(req: CheckRequest):
```

```
# nothing stops one client calling this
# ten thousand times a minute
return predict(req.text)
```

###### **The attack** 

A script sends thousands of requests, to wear the service down or to map exactly where the model's decision changes. 

##### **The fix, in principle** 

Count requests per client and refuse the excess with status 429, for example with a library such as slowapi. Pick a limit a real user never reaches. 

###### **In the wild** 

OWASP's API Security Top 10 (2023) lists Unrestricted Resource Consumption as API4. Tramèr et al. (2016) copied models from BigML and Amazon Machine Learning almost perfectly, just by querying their prediction APIs. 

OWASP API Security Top 10 2023. Tramèr et al. (2016), USENIX Security Symposium. 



<!-- Start of picture text -->
BUR gages<br>*NE*<br><!-- End of picture text -->



<!-- Start of picture text -->
' UNION SELECT username, password FROM users--<br>SELECT name, description FROM products WHERE category<br>= 'Gifts' UNION SELECT username, password FROM users--<br>bi SUBMIT =a<br>\y y/ |__| a<br>\ ae I/<br>——— %* All passwords<br>cd All usernames<br><!-- End of picture text -->



<!-- Start of picture text -->
SWIN | coum<br>BUR | wasn:<br>*NE*<br><!-- End of picture text -->

SQL Injection 

**INTERMEDIATE** up to 3 marks 

### **SQL injection** 

Once you store data in a database, such as a history of past checks. 

```
# the input becomes part of the SQL text
query = ("SELECT * FROM checks "
"WHERE username = '" + name + "'")
db.execute(query)
```

**The attack** **`' OR '1'='1`** The quote closes the string early, and the condition becomes true for every row. 

##### **The fix, in principle** 

Pass input as a parameter, or use an ORM such as SQLAlchemy, so it is always data and never part of the query, as in db.execute("SELECT * FROM checks WHERE username = ?", (name,)). 

###### **In the wild** 

From 27 May 2023 the CL0P ransomware gang exploited a SQL injection flaw in MOVEit Transfer (CVE-2023-34362). Emsisoft counted more than 2,700 organisations and 95 million people affected. 

CISA (2023) Advisory AA23-158A. Emsisoft (2023, updated 2024) MOVEit breach statistics. 



<!-- Start of picture text -->
BUR gages<br>*NE*<br><!-- End of picture text -->

**INTERMEDIATE** up to 3 marks 

### **Unsafe file upload** 

Whenever you accept files, such as logs, images or audio. It goes beyond the size limit in section 2.3. 

```
# saved under the name the user chose,
# and read whole with no size check
path = "uploads/" + file.filename
with open(path, "wb") as f:
f.write(await file.read())
```

**The attack** 

```
filename ../../app/main.py
```

The file lands outside the upload folder, and can overwrite your own code. 

##### **The fix, in principle** 

Enforce the size on the back end as you read, save every file under a name you generate yourself, and check that its contents really match the type you expect. 

###### **In the wild** 

In June 2018 Snyk disclosed Zip Slip, a path traversal flaw in archive extraction where entries named like ../../evil.sh land outside the target folder. It affected thousands of projects. 

Snyk (2018) Zip Slip vulnerability. OWASP File Upload Cheat Sheet. 



<!-- Start of picture text -->
BUR gages<br>*NE*<br><!-- End of picture text -->

**INTERMEDIATE** up to 3 marks 

### **Misconfiguration and vulnerable dependencies** 

Every application. Safe settings are rarely the default, and you run far more code than you wrote. 

`# debug mode returns full tracebacks` **The attack** `# to anyone who triggers an error app = FastAPI(debug=True)` Attackers scan for servers left in debug mode, `# and every library you install` missing security headers, and libraries with known `# can carry a known vulnerability` flaws. 

##### **The fix, in principle** 

Turn debug features off and set security headers. Run pip-audit and npm audit, scan the running application with OWASP ZAP, then fix or justify each finding. 

###### **In the wild** 

Apache fixed Struts flaw CVE-2017-5638 on 7 March 2017. Equifax had not patched it, and from 13 May attackers stole data on about 147 million people. In 2021 Log4Shell (CVE-2021-44228) scored the maximum CVSS of 10.0. 

US GAO (2018) GAO-18-559. Apache Log4j security vulnerabilities page. 



**ADVANCED** up to 4 marks 

### **Denial of service** 

Every application, because running a model costs far more than sending a request. 

##### **Slow work in async def** 

One slow request holds up every other user until it finishes. 

##### **A crafted, expensive input** 

Text that makes a regular expression backtrack can take seconds of CPU. 

##### **A decompression bomb** 

A 118 KB image can take 300 MB of memory once decoded. 

##### **What is in scope** 

A distributed flood from many machines is stopped upstream by a hosting provider or a content delivery network, and cannot be tested fairly on one laptop. Your back end should defend against one request that costs it far more than it costs the attacker. 

###### **In the wild** 

On 2 July 2019 one regular expression in a Cloudflare firewall rule backtracked enormously. It exhausted CPUs across Cloudflare's global network and caused errors for 27 minutes. 

Cloudflare (2019) Details of the Cloudflare outage on July 2, 2019. 



<!-- Start of picture text -->
BUR | Yesens<br>*NE*<br><!-- End of picture text -->

**ADVANCED** up to 4 marks 

### **Where the slow work runs** 

FastAPI runs a plain def endpoint in a threadpool. Slow work inside async def holds up every other request. 

`@app.post("/check") @app.post("/check") async def check(req: CheckRequest): def check(req: CheckRequest): # slow, and on the event loop # runs in a threadpool instead return predict(req.text) return predict(req.text)` **async def, slow work on the event loop** every other request waits until it finishes **plain def, slow work in a threadpool** other requests are still answered 

##### **The fix, in principle** 

Keep slow work off the event loop, limit what a single input may cost, and cap how many requests run at once, so the excess is refused with 503 instead of the server freezing. 

FastAPI documentation, Concurrency and async / await. Python documentation, Developing with asyncio. 



<!-- Start of picture text -->
BUR gages<br>»NE#<br><!-- End of picture text -->



<!-- Start of picture text -->
KES) @)<br>Vany,<br>SQQP WEBSITE i coeAB eS<br>Si 3<br>Aj mp ti ca SR<br><!-- End of picture text -->



**Server-side request forgery (SSRF)** 

**ADVANCED** up to 4 marks 

### **Server-side request forgery (SSRF)** 

Only if your back end makes a request based on the input, such as fetching a page or looking up a domain. 

```
import requests
# fetches whatever address the user sends
page = requests.get(req.url, timeout=5)
```

**The attack** **`http://127.0.0.1:8000/admin http://169.254.169.254/`** 

The server visits internal addresses on the attacker's behalf, places the attacker could never reach directly. 

##### **The fix, in principle** 

Decide which destinations your back end may contact, and refuse everything else, internal and private addresses above all. 

###### **In the wild** 

In 2019 an attacker used SSRF through Capital One's misconfigured web application firewall to reach the AWS metadata service, steal credentials and copy data on about 106 million people. 

Capital One (2019) Information on the Capital One Cyber Incident. Krebs, B. (2019) What We Can Learn from the Capital One Hack. 



**ADVANCED** up to 4 marks 

### **Broken access control** 

Only once you add user accounts. Being logged in is not the same as being allowed to see a record. 

```
@app.get("/history/{check_id}")
def read_check(check_id: int,
user=Depends(current_user)):
# logged in, yes, but whose check is it?
return db.get(Check, check_id)
```

**The attack** **`GET /history/42`** Logged in as user B, ask for check 42, which belongs to user A. The server returns it. 

##### **The fix, in principle** 

Check on every request that the record belongs to the user asking, not only that someone is logged in, so another user's record is simply not found. 

###### **In the wild** 

Broken Access Control ranks first in the OWASP Top 10, in both 2021 and 2025. In Australia, the regulator ACMA alleges that a coding error broke access controls in the 2022 Optus breach, which affected about 9.5 million people. OWASP Top 10 2021 and 2025. OAIC (2025). CSO Online (2024), reporting ACMA's case. 



<!-- Start of picture text -->
BUR gages<br>*NE*<br><!-- End of picture text -->

# Reference Links 

**<u>https://portswigger.net/web-security/sql-injection https://portswigger.net/web-security/ssrf https://portswigger.net/web-security/os-command-injection https://portswigger.net/web-security/file-upload https://portswigger.net/web-security/file-path-traversal https://portswigger.net/web-security/access-control</u>** 



<!-- Start of picture text -->
SWIN | coum<br>»NE#<br><!-- End of picture text -->

### **Choosing your two** 

Start from your threat model. Each topic has a natural place to start. 

|**Prompt injection guardrail**|SQL injection, because every input is itself an attack string, easily stored in a history of past<br>checks.|
|---|---|
|**Phishing URL detection**|SSRF and command injection, where lookups such as WHOIS are tempting to add.|
|**AI-generated content detection**|Rate limiting, where people may probe the detector again and again.|
|**Log anomaly detection**|Unsafe file upload for log files, and denial of service when large files are slow to parse.|



Denial of service and misconfiguration apply to every application, so every topic has a route to full marks. If you choose both rate limiting and denial of service, each must rely on a different mechanism. 



<!-- Start of picture text -->
BUR | Yesens<br>*NE*<br><!-- End of picture text -->

### **How each defence is marked** 

The level sets the maximum. Quality decides where you land. 

##### **Effectiveness** 

It stops the attack, and its obvious variations. 

##### **Evidence** 

Your video shows the attack succeeding without the defence, and failing with it. 

##### **Reasoning** 

Your threat model justifies it, and you explain what it costs. 

##### **What costs marks** 

A defence that an obvious variation can get past, or that is shown working without the attack, earns less. A defence that does not appear in your video earns nothing. 

Only the two defences named in your README are marked, so building a third earns nothing extra. 



<!-- Start of picture text -->
BUR | Yesens<br>*NE*<br><!-- End of picture text -->

### **Prove it by attacking your own application** 

The same four steps for every defence, all in your video. 

**1 2 3 4 Attack it Add the defence Attack again Try a variation** without the defence, and and explain the idea behind with the same request, and of your own, and show it fail show it succeed it show it fail too 

Send requests straight to the back end with curl, Postman or the /docs page. 

##### **Only your own application** 

All security testing in this assignment is limited to your own application, running on your own machine. Never test any system you do not own, including another group's application. 



### **What to take away** 

**The back end is where security lives** Attackers send requests directly, so the checks that matter run on the back end. **Do the basics first** The four hygiene requirements in section 2.3 are required of every group. **Threat model before defences** Who would attack, what they want, what they can do, and which risks your design really has. **Know each risk and the idea behind its fix** The level caps the marks. Quality decides the rest. **Prove every defence** Attack without it, add it, attack again, try a variation, all in your video. 



<!-- Start of picture text -->
BUR [ilies<br>*NE*<br><!-- End of picture text -->

### **Coming up** 

##### **In the seminar this week** 

FastAPI hands-on. Endpoints, Pydantic models, status codes, one consistent error format, CORS and size limits. 

##### **In next week's lecture** 

Advanced security in section 2.8. Side channels, attacks on the model, and measuring a defence before and after. 

Start your threat model now. It decides which two defences are worth your time. 



<!-- Start of picture text -->
BUR | Yesens<br>*NE*<br><!-- End of picture text -->

### **References** 

|Shostack, A. (2014) Threat Modeling: Designing for Security. Wiley.|
|---|
|Shostack, A. (n.d.) Shostack's Four Question Framework. github.com/adamshostack/4QuestionFrame|
|OWASP (2021) OWASP Top 10 2021. owasp.org/Top10/2021|
|OWASP (2025) OWASP Top 10 2025. owasp.org/Top10/2025|
|OWASP (2023) OWASP API Security Top 10 2023, API4:2023 Unrestricted Resource Consumption. owasp.org/API-Security|
|OWASP (n.d.) File Upload Cheat Sheet. cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html|
|OWASP (n.d.) Command Injection. owasp.org/www-community/attacks/Command_Injection|
|PortSwigger (n.d.) OS command injection. Web Security Academy. portswigger.net/web-security/os-command-injection|
|Python Software Foundation (n.d.) pickle — Python object serialization. docs.python.org/3/library/pickle.html|
|joblib developers (n.d.) joblib.load. joblib.readthedocs.io/en/stable/generated/joblib.load.html|
|FastAPI (n.d.) Concurrency and async / await. fastapi.tiangolo.com/async|





### **References, continued** 

JFrog (2024) Data Scientists Targeted by Malicious Hugging Face ML Models with Silent Backdoor. jfrog.com/blog Tramèr, F., Zhang, F., Juels, A., Reiter, M.K. and Ristenpart, T. (2016) Stealing machine learning models via prediction APIs. 25th USENIX Security Symposium, pp. 601–618. 

CISA (2023) #StopRansomware: CL0P Ransomware Gang Exploits CVE-2023-34362 MOVEit Vulnerability, AA23-158A. cisa.gov Emsisoft (2023, updated 2024) Unpacking the MOVEit Breach: Statistics and Analysis. emsisoft.com/en/blog/44123 Snyk (2018) Zip Slip Vulnerability. security.snyk.io/research/zip-slip-vulnerability US Government Accountability Office (2018) Data Protection: Actions Taken by Equifax and Federal Agencies in Response to the 2017 Breach, GAO-18-559. gao.gov/products/gao-18-559 Apache Software Foundation (n.d.) Security, Apache Log4j. logging.apache.org/log4j/2.x/security.html Cloudflare (2019) Details of the Cloudflare outage on July 2, 2019. blog.cloudflare.com Capital One (2019) Information on the Capital One Cyber Incident. capitalone.com/digital/facts2019 Krebs, B. (2019) What We Can Learn from the Capital One Hack. krebsonsecurity.com OAIC (2025) Australian Information Commissioner takes civil penalty action against Optus. oaic.gov.au Sarraf, S. (2024) Optus breach occurred due to a coding error, alleges ACMA. CSO Online. csoonline.com 



