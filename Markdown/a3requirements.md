# Assignment 3 

#### Start Assignment 

Due 8 Nov by 23:59 

Points 45 

Submitting a file upload 

|**Assignment**<br>**Name**|Full-Stack Web Development for a Secure AI Application|
|---|---|
|**Assignment**<br>**Description**|In this final assignment, you turn a trained model into a full-stack web application that people can use and that holds up when<br>someone tries to misuse it. The front end must be built with React and the back end with FastAPI. A user provides input through<br>the front end, the back end runs it through your model, and the result comes back to the user clearly and safely.<br>Treat your model as a black box that takes an input and returns a prediction. You may use your Assignment 2 model, or any<br>model you train for your topic.**This assignment does not mark your model's accuracy.**It marks how well you build, connect,<br>and protect the application around the model, so a weaker model from Assignment 2 will not cost you marks here.<br>Every topic in this unit is a cybersecurity problem, which means your application will receive hostile input by design. Making it<br>secure is the focus of this assignment, and the main route to the highest marks.<br>As the final assignment of the unit, this project carries the largest weight. It tests whether you can build a complete web<br>application, connect a model to it, handle errors and hostile input safely, and explain clearly how all of it works.|
|**Weight**|45% of your total marks for the unit|
|**Due Date**|Sunday 8 November 2026, 11:59 pm (Week 13)|



|**Submission**|�.**Source code**(ZIP), including your README and your model file<br>2.**Video**(MP4 or AVI), 15 minutes maximum<br>3.**Meeting minutes**(PDF)<br>4.**Contribution form**(PDF)|
|---|---|
||There is no written report. Section 3 describes each deliverable.|
||Any submission after the due date counts as late. For the first 3 days late, no marks are deducted. From the fourth day, 5% of<br>the available mark is deducted for each calendar day or part thereof.|
|Late<br>Penalties|Monday 9 to Wednesday 11 November, late, but no marks deducted<br>Thursday 12 November, 5% deducted<br>Friday 13 November, 10% deducted<br>Saturday 14 November, 15% deducted<br>Sunday 15 November, 20% deducted|
||Submissions more than 7 calendar days late are not accepted. If serious circumstances mean you need more time than this,<br>email your tutor and Lecturer as soon as possible to request an extension.|



# **1. Project Description** 

This project develops a complete machine learning solution to a real cybersecurity problem, combining project management, design and technical implementation. Your team works through three phases, planning the project in Assignment 1, building and evaluating a model in Assignment 2, and delivering it as a secure web application in this assignment. 

Your topic is the one your team has worked on all semester: one of prompt injection guardrail, AI-generated content detection, phishing URL detection, and log anomaly detection. 

# **2. Overview of the tasks** 

Sections 2.1 to 2.5 apply to every topic. Together they describe a complete, working application. 

## 2.1 Front end (React.js) 

The front end is what users and markers see first, so it must work well and look professional. 

An input form that validates input before anything is sent to the back end 

- Results shown clearly with the model's confidence, and the result as the most prominent element on screen 

- Visible loading, success and error states, so the user always knows what is happening 

- Error pages, including a page for addresses that do not exist and a fallback page when something fails unexpectedly, so the user never sees a blank screen 

- At least two visualisations, each answering a different question about the results, with clear titles, labels and legends, and tooltips at minimum A consistent visual design throughout, with one colour scheme, consistent typography and spacing, and a clear layout 

- A responsive layout that works on both a desktop and a phone-sized screen 

Basic accessibility, with a label on every input, readable colour contrast, and every function usable by keyboard 

For a topic that checks one input at a time, one visualisation can show the current result while another compares all the inputs checked in the current session. More charts do not earn more marks. Each one should help the user understand something the others do not. 

## 2.2 Back end (FastAPI) 

- Request and response models defined with Pydantic 

- At least two HTTP methods, each used for a genuine purpose 

- Correct HTTP status codes, and clear error messages when input is invalid 

- Every error, including unexpected ones, returned in one consistent JSON format, without internal details such as stack traces The model loaded once when the server starts, not on every request 

## 2.3 Security hygiene 

These are the minimum expected of any application in a cybersecurity unit. None of them takes much work, and an application that misses them cannot reach the higher grades. 

- User input is never rendered as HTML 

- Text inputs and file uploads have a size limit, enforced on the back end 

- CORS allows only your own front end, not every origin 

- Passwords, keys and other secrets are kept out of your source code, for example in environment variables 

React escapes text for you, so the first requirement holds as long as you never bypass it, for example with `dangerouslySetInnerHTML` to highlight words. React 19 and later also neutralise a `javascript:` link written into `href` <mark>,</mark> but earlier versions at most print a warning, and no version protects a URL passed to `window.open` or assigned to `window.location` . 

## 2.4 Running the application 

The whole application starts from your README on a clean machine 

Dependency versions are pinned, so the application runs the same way for the marker as it does for you 

## 2.5 Requirements for your topic 

You decide what your application takes as input, whether that is text, a URL, an image, audio, a log file, or a combination, so that it suits the model you are deploying. What your topic decides is what the application must show at minimum. 

|**Topic**|**The application shows at minimum**|
|---|---|
|Prompt<br>injection<br>guardrail|Whether the input is allowed or blocked, with<br>confidence|
|AI-generated<br>content|Whether the content is AI-generated or human-made,<br>with confidence|



|detection||
|---|---|
|Phishing URL<br>detection|Whether the input is phishing or legitimate, with<br>confidence|
|Log anomaly<br>detection|Each session with an anomaly score, an overall<br>summary, and a detail view for any session the user<br>selects|



## 2.6 Threat model 

Before you defend your application, decide what you are defending it against. Write a short threat model that answers three questions. 

- �. Who would want to attack your application? 

2. What are they trying to achieve? 

3. What can they actually do to it? 

Your answers decide which defences matter most, and you should use them to justify the choices you make in section 2.7. Half a page in your README is enough, and you should summarise it in your video before demonstrating your defences. 

Each topic suggests a natural starting point. 

|**Topic**|**A likely attacker, and what they want**|
|---|---|
|Phishing||
|URL|A phisher who wants their link to pass as legitimate|
|detection||
|Prompt|An attacker who wants an injection to get past the|



|injection<br>guardrail|guardrail|
|---|---|
|AI-generated<br>content<br>detection|Someone who wants AI-generated content to be<br>judged human-made|
|Log anomaly<br>detection|An intruder who wants their activity hidden among<br>normal logs, using log lines that may themselves carry<br>malicious content|



## 2.7 Innovation. Security defences 

Innovation in this assignment means defending your application against the attacks your threat model identifies, and proving each defence works by attacking your own application. 

One principle runs through all of this. **Front-end checks are for usability. Back-end checks are for security.** Attackers do not use your interface, so several of the attacks below can only be demonstrated by sending requests directly, with a tool such as curl or Postman. 

Not every risk applies to every application. An application whose back end never makes outbound requests cannot suffer SSRF, and one without a database cannot suffer SQL injection. Part of your threat model is working out which risks your design actually exposes, and saying briefly why the others do not apply. 

Each risk below has a level, which sets the most a defence against it can earn. A Basic defence can earn up to 2 marks, an Intermediate one up to 3, and an Advanced one up to 4. Levels reflect how much work a defence takes to build and demonstrate, not how serious the risk is. 

|**Risk**|**Level**|**When it applies to your application**|**How to prove you have stopped it**|
|---|---|---|---|
|Unsafe model|Basic|Whenever you load a model with<br>`joblib`or<br>`pickle`,both of which can|Check the model file's hash when the|



|loading||execute code hidden in the file. It matters most when the model file<br>comes from a download script or from someone else|server starts, and refuse to load it if the<br>hash does not match|
|---|---|---|---|
|Command<br>injection|Basic|Whenever your back end runs a system command, such as the<br>`whois`<br>tool. Pasting the input into a shell command lets input such as<br>`example.com; ls` run commands of the attacker's choosing|Submit a crafted input with curl and show<br>the extra command never runs, because<br>the input is validated and passed as a list<br>of arguments, never through a shell|
|Missing rate<br>limiting|Basic|Every application. FastAPI sets no limit, so anyone can flood the API<br>or probe how the model makes its decisions|Send rapid requests and show the limit is<br>enforced|
|SQL injection|Intermediate|Once you store data in a database, such as a history of past checks.<br>Building a query by pasting the input into the SQL text lets input such<br>as<br>`' OR '1'='1`change what the query does|Submit a crafted input with curl, show it is<br>stored and returned as plain data, and<br>show that every query passes input as a<br>parameter or through an ORM such as<br>SQLAlchemy|
|Unsafe file<br>upload|Intermediate|Whenever you accept files. FastAPI does not limit upload size for you,<br>and saving a file under the user's own filename lets<br>`../` write outside<br>the upload folder. A size limit alone is already required by section 2.3,<br>so this defence must go further|Send an oversized file, a crafted filename,<br>and a file whose contents do not match its<br>type with curl, and show all three are<br>rejected|
|Misconfiguration<br>and vulnerable<br>dependencies|Intermediate|Every application. Security headers are not set by default, debug<br>features are easy to leave on, and any library can carry a known<br>vulnerability|Run<br>`pip-audit` and<br>`npm audit`,scan the<br>running application with OWASP ZAP,<br>then fix or justify each finding|
|Denial of|Advanced|Every application, because running a model costs far more than|Send one deliberately expensive request|



|service||sending a request. Slow inference inside an<br>`async def`endpoint make<br>every other user wait until it finishes, and a small crafted input can<br>cost far more than it looks, such as text that makes a regular<br>expression backtrack, or a 118 KB image that takes 300 MB of<br>memory once decoded|s<br>and show that other requests are still<br>answered promptly, then send many at<br>once and show the application rejects the<br>excess with a 503 error instead of freezing|
|---|---|---|---|
|Server-side<br>request forgery<br>(SSRF)|Advanced|Only if your back end makes a request based on the input, such as<br>fetching a page, looking up a domain, or downloading an image from<br>link|a<br>Submit inputs that point at internal<br>addresses, such as<br>`127.0.0.1`or a link<br>that redirects there, and show from your<br>back-end logs that no such request is<br>made|
|Broken access<br>control|Advanced|Only once you add user accounts. User B may then fetch user A's<br>records by requesting them directly|Logged in as user B, request one of user<br>A's record IDs with curl, and show the<br>request is refused|



A distributed denial-of-service attack, where many machines flood your network at once, is stopped upstream by a hosting provider or a content delivery network rather than by application code, and it cannot be tested fairly on a single laptop. What your back end can and should defend against is a request that costs it far more to handle than it costs an attacker to send. 

Each topic has a natural place to start. SQL injection suits prompt injection, because every input is itself an attack string and is easily stored in a history of past checks. SSRF and command injection suit phishing, where lookups such as WHOIS are tempting to add. File upload suits any application that accepts files, such as log files, images or audio. Rate limiting suits AI-generated content detection, where people may probe the detector repeatedly. Denial of service suits any application whose inference is slow, such as one using a deep learning model or parsing large log files. Denial of service and misconfiguration apply to every application, so every topic has a route to full marks. 

Choose up to two defences, from risks your application actually has, and name them in your README. Only those two are marked, so building more earns nothing extra. Your two defences together are capped at 8 marks, so full marks for this section need one Advanced defence together with an Intermediate or Advanced one. You may choose two Advanced defences, but the total is still capped at 8 marks. 

Each defence is marked on its quality, up to the value of its level. The highest marks go to a defence that stops the attack and its obvious variations, is shown in your video with the attack succeeding without the defence and failing with it, is justified by your threat model, and has its cost explained. A defence that an obvious variation can get past, or that is shown working without the attack, earns less. A defence that does not appear in the video earns nothing. 

If you choose both rate limiting and denial of service, each must rely on a different mechanism. A justified innovation of your own can take the place of one of the two, and your tutor will decide its level by the same standard. Security is still the recommended direction. 

## 2.8 Advanced security 

This part goes beyond typical undergraduate work and is aimed at groups who want the highest marks. These attacks exploit the fact that a trained model sits behind an API, however accurate the model is. Choose one, name it in your README, and do it properly. Only one is marked. 

**Side channels.** A side channel leaks information through something other than the response itself, such as how long the response takes or how large it is. An application can therefore give its answer away even when the visible response reveals nothing. 

|**Attack**|**What it looks like in this application**|**What to measure**|
|---|---|---|
|Timing side<br>channel in|<br>Every response looks the same, but some take longer, for example because<br>blocked reuests do extra work so an attacker can infer the outcome from|The response-time distribution for each outcome,|
|the<br>decision|q   ,<br>timing alone|before and after you make response times uniform|
|Cache<br>timing side<br>channel|If you cache results to speed up repeated inputs, a cached answer returns far<br>faster, so anyone can tell whether another user has already checked a given<br>input. In our test, a cached answer took about 2 ms and a new one about 17<br>ms, with no overlap at all|Response times for inputs other users have<br>submitted against new inputs, before and after you<br>scope the cache to each user or remove the<br>difference|
|Response|Responses that differ in size by outcome reveal the outcome even to someone|The response size for each outcome, before and|



|size side<br>channel|who cannot read them. HTTPS hides the content of a response but not its<br>length. In our test, an allowed response was 21 bytes and a blocked one 118<br>bytes|after you return the same fields at the same size<br>for every outcome|
|---|---|---|
|Login<br>timing side<br>channel|Only once you add user accounts. If the password check runs only for<br>usernames that exist, a failed login reveals which usernames are real. In our<br>test, a real username took about 490 ms to reject and an unknown one under 2<br>ms|Response times for real and unknown usernames,<br>before and after you always run the password<br>check, against a dummy hash when the username<br>does not exist|



Some side channels are created by defences elsewhere in this specification. A cache that protects you against denial of service is exactly what creates the cache timing side channel, so if you add one, check whether it leaks. 

#### **Attacks on the model through its API.** 

|**Attack**|**What it looks like in this application**|**What to measure**|
|---|---|---|
|Membershi<br>inference|p<br>The model's confidence reveals whether a particular<br>example was in its training data|Attack accuracy compared with the 50% of<br>random guessing, before and after your<br>defence|
|Model<br>extraction|Repeated queries let an attacker train a copy of your<br>model|How closely the copy agrees with your<br>model as the number of queries grows, with<br>and without your defence|
|Detection<br>evasion|Small changes, such as swapping letters for look-alike<br>Unicode characters, change what the model sees without<br>changing what a person sees|The evasion success rate, before and after<br>you normalise input before it reaches the<br>model|



Four conditions apply to this part. 

- **Measure before and after.** Implement the attack, measure it, add your defence, and measure again. A claim without numbers earns no marks, because the obvious defence does not always work. Hiding the model's confidence and returning only a label, for example, does far less to stop model extraction than you might expect. 

- **Secure the basics first.** This part only counts once your application meets the security hygiene requirements in section 2.3. 

- **Explain what the defence costs.** Uniform response times slow the application down, hiding confidence gives the user less information, and a cache scoped to each user saves less work. Say what you gave up and why it was worth it. 

- **Attack only your own application, on your own machine.** 

### Suggested reading 

- **<u>OWASP Top 10 (https://owasp.org/www-project-top-ten/)</u>** , the standard list of the most critical web application security risks Bortz, A. and Boneh, D. (2007) ' **<u>Exposing private information by timing web applications (https://crypto.stanford.edu/~dabo/abstracts/</u>** 

- **<u>webtiming.html)</u>** ', in _Proceedings of the 16th International Conference on World Wide Web_ . ACM, pp. 621–628. 

- Chen, S., Wang, R., Wang, X. and Zhang, K. (2010) ' **<u>Side-channel leaks in web applications: a reality today, a challenge tomorrow</u> (https://www.microsoft.com/en-us/research/?p=158925)** ', in _2010 IEEE Symposium on Security and Privacy_ . IEEE, pp. 191–206. 

- Shokri, R., Stronati, M., Song, C. and Shmatikov, V. (2017) ' **<u>Membership inference attacks against machine learning models (https:// www.comp.nus.edu.sg/~reza/files/Shokri-SP2017.pdf)</u>** ', in _2017 IEEE Symposium on Security and Privacy_ . IEEE, pp. 3–18. Tramèr, F., Zhang, F., Juels, A., Reiter, M.K. and Ristenpart, T. (2016) ' **<u>Stealing machine learning models via prediction APIs (https:// usenix.org/conference/usenixsecurity16/technical-sessions/presentation/tramer)</u>** ', in _Proceedings of the 25th USENIX Security Symposium_ . USENIX Association, pp. 601–618. 

# **3 Deliverables** 

There is no written report. Everything a report would have covered now lives in your README, your API documentation, and your video. 

- �. **Source code (ZIP).** Front end and back end in separate folders. Include your model file, or a download script if it is too large to upload. Leave out `node_modules` . 

2. **README.** Setup and run instructions, an architecture diagram, your pinned dependency versions, your threat model, references in Harvard style, a statement of how you used generative AI, and the defences and advanced attack you want marked. 

3. **API documentation.** Use the `/docs` page that FastAPI generates for you. Make sure every endpoint has a description and an example request and response. 

4. **Video, 15 minutes maximum.** See section 3.1. 

5. **Meeting minutes (PDF).** At least one meeting each week since your team formed. You can use the attached meeting minutes as they are or as a reference to create your own. **<u>Meeting Minutes Example.docx (https://swinburne.instructure.com/courses/77371/files/44766619?wrap=1)</u>** 

6. **Contribution form (PDF).** Download and complete Group Assessment Contribution Form.docx. You can download the form **<u>Group Assessment Contribution Form.docx (https://swinburne.instructure.com/courses/77371/files/44767255?wrap=1)</u> (https://** 

**swinburne.instructure.com/courses/77371/files/44767255/download?download_frd=1)** 

## 3.1 Video presentation 

Your video is the main way your work is assessed, so plan it as carefully as the application itself. You decide how to structure it and how long to spend on each part, within the 15-minute maximum. Whatever structure you choose, the video must clearly explain the following. 

- Who the application is for, and what problem it solves 

The full workflow from input to result, demonstrated live, including invalid input, error pages, and the phone-sized layout 

- How the parts of your code connect, following one request from the front end through your API and model and back, shown in your actual code and in `/docs` 

How the key parts are implemented, walking through the code itself rather than only slides, and explaining in your own words what it does and why you wrote it that way 

The key design decisions you made, and why you made them 

Your threat model, how the application handles malicious input, and for any attack or defence you built, how the attack works and how your code stops it, demonstrated by attacking your own application 

What does not work yet, and what you would do next 

Anything you want marked must appear in the video, because markers assess your work mainly from it. 

The video is also marked in its own right, for how well you show that you understand your own work and why it is built the way it is. If you cannot explain part of your application, you lose marks here even if that part works. A missing feature loses marks only under the application criteria, not 

#### here as well. 

- Your team decides who presents. Not every member has to appear in the video. 

- If your file exceeds the Canvas upload limit, upload it to YouTube as an unlisted video, submit the link in a text file named `group-name-videolink.txt` <mark>,</mark> and keep the link active until marking is complete. 

If the video cannot be opened at the time of marking, most components of this assignment will receive zero. Check that it plays before you submit. 

# **4. Submission** 

Submit through the Assignment 3 Submission link on Canvas by Sunday 8 November 2026, 11:59 pm (Week 13). No hard copy is required. Only one member of each group submits, and that member submits all the files. 

**File naming.** Name every file with your group name, for example `session-xx-group-1-A3-video.mp4` . Marks may be deducted if naming and file requirements are not followed. Submissions by email are not accepted. 

|**Deliverable**|**Format**|
|---|---|
||One ZIP file, with front end and back<br>end in separate folders, and the|
|Source|README in Markdown or PDF.|
|code|Include your model file in the back-|
||end folder, or a download script if it is<br>too large to upload.|



|Video|MP4 or AVI, 15 minutes maximum, or<br>an unlisted YouTube link in<br>`group-`<br>`name-video-link.txt`|
|---|---|
|Meeting<br>minutes|PDF|
|Contribution<br>form|PDF|



# **5. Marking Criteria** 

The full rubric is provided separately. The table below shows how the grade levels relate to the requirements in this specification. This table is guidance only. Completing the parts listed for a level does not guarantee that grade. At every level, marks reward the reasoning behind your choices, not the number of features you build. 

|Pass to<br>Credit|An application that works end to end, meets the security hygiene<br>requirements, shows results clearly and runs from its README|
|---|---|
|Distinction|All of the above done well, with robust error handling, a clean API<br>and codebase, a polished and consistent interface with interactive<br>visualisations, and a video that explains your own code clearly, plus<br>at least one defence from section 2.7|
|High|Two defences from section 2.7 done well, either two Intermediate|



