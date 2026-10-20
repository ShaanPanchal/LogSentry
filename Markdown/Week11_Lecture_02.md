



COS30049 – Computing Technology Innovation Project 

Week 11 – Building a Full-Stack Application (Debugging and Ensuring Code Quality) 



( Lecture – 02 ) 

Ningran Li (Icey) <u>ningranli@swin.edu.au</u> 



## Acknowledgement of Country 

We respectfully acknowledge the Wurundjeri People of the Kulin Nation, who are the Traditional Owners of the land on which Swinburne’s Australian campuses are located in Melbourne’s east and outer-east, and pay our respect to their Elders past, present and emerging. 

We are honoured to recognise our connection to Wurundjeri Country, history, culture, and spirituality through these locations, and strive to ensure that we operate in a manner that respects and honours the Elders and Ancestors of these lands. 

We also respectfully acknowledge Swinburne’s Aboriginal and Torres Strait Islander staff, students, alumni, partners and visitors. 

We also acknowledge and respect the Traditional Owners of lands across Australia, their Elders, Ancestors, cultures, and heritage, and recognise the continuing sovereignties of all Aboriginal and Torres Strait Islander Nations. 





<!-- Start of picture text -->
Y i, ‘ ry)<br><!-- End of picture text -->



<!-- Start of picture text -->
i 1 oo4 1 4 ee ee 1 1 4<br><!-- End of picture text -->

- **Recap Front-end & Back-end** 

- **React API Call** 

- **Data Visualization** 

- **Full-stack integration** 

- **Debugging and Troubleshooting** 

- **Best Practices in Code Development** 



<!-- Start of picture text -->
d ‘<br>AZe $ a<br>Gee 2 _&<br>a?<br><!-- End of picture text -->

Image from [Pinterest] 



<!-- Start of picture text -->
BUR<br>*NE-<br><!-- End of picture text -->

# Introduction to Debugging 

### **What is Debugging?** 

- The process of identifying, analyzing, and removing errors (bugs) in software code 

- • Essential skill for developers to ensure software functions correctly 

### **Why is Debugging Important?** 

- Improves software quality and reliability 

- Saves time and resources in the long run 

- Enhances understanding of the codebase 

### **Types of Bugs** 

- Syntax Errors: Incorrect code structure 

- Runtime Errors: Occur during program execution 

- Logical Errors: Produce incorrect results without crashing 

### **Debugging Process Overview** 



Image from [Pinterest] 

- 1. Reproduce the issue 

- 2. Locate the source of the problem 

- 3. Analyze the cause 

- 4. Fix the bug 



<!-- Start of picture text -->
SWIN<br>BUR<br>*NE-<br><!-- End of picture text -->

- 5. Test the solution 

# Debugging Tools for React 

### **Browser Developer Tools (F12)** 

- Elements tab: Inspect and modify DOM 

- Console: View logs, errors, and warnings 

- Sources: Set breakpoints and debug JavaScript 

- Network: Monitor network requests and responses 



<!-- Start of picture text -->
$30049-Computing Technology Inno. 53 View as Student Ik tie :<br>2024-HS2-COS30049- ; a, am SLI<br>Computing Technology Assignto ‘Edit vey sen.<br>Innovation Project 3 coree<br>gett! — »<br>SWINBURNE Aer) —_—— aety cova, ne II<br>Welcome to COS30049: Computing Technology Innovation i<br>Project. ; ti Dot<br>This isa project-based unit where students collaborate in teams to develop innovative<br>solutionsfor industry challenges. The primary focus isto apply a rangeof IT techniques F a<br>and analysis methods to effectively address these challenges. Each team will be supported pase<br>by a designated staff member acting as a facilitator, guiding them in creating automatic sts<br>tools or platforms with instructions that cater to diverse ICT backgrounds. The goal is for a<br>students to learn how to complete3 real-world project fromscratch, similar to what mre<br>industrial professionals<br>do daity nace<br>here<br>Throughout this unit, we will focus on Al technology as the central theme for the projects.<br>Students will choose their topic from several provided options and use the Al technology bows<br>they learn during the semester to develop a website that showcases their chosen topic wears<br>Adéisonally, students will need to apply project management techniques to manage their Re renner era sree rere err ry ‘noua<br>work effectively , = x ‘<br><!-- End of picture text -->



<!-- Start of picture text -->
Swi N<br>BUR :<br>~NE=<br><!-- End of picture text -->

# Debugging Tools for React 

#### **React Developer Tools** 

- Browser extension for debugging React applications 

- Components tab: Inspect component hierarchy and props 

- Profiler tab: Analyze component render performance 

#### **IDE Debugging Features** 

- Syntax Errors: Incorrect code structure 

- • Runtime Errors: Occur during program execution 

- Logical Errors: Produce incorrect results without crashing 

#### **Console Logging** 

- `console.log()`: Output variable values and messages 

- `console.error()`: Log error messages 

- `console.warn()`: Log warning messages 

- `console.table()`: Display tabular data 



<!-- Start of picture text -->
[8 Elements Console Sources Network Performance + Memory —_ Application 14152 @ i x<br>= 85;<br>User's name is: Henry yoi2i8:3<br>User Henry has scored 85 points. ywa2168:5<br>{<br>Error i;<br>} (error) {<br>,<br>> Error message: Something went wrong! yaazz2e4<br>(age ye < 18)= 16;{<br>,<br>A > User is under 18, some features may be restricted. ym1226:3<br>h { na + age: 35, city ,<br>(index) rane age city<br>» Array(3)<br><!-- End of picture text -->



<!-- Start of picture text -->
SWIN .<br><!-- End of picture text -->

# Debugging Techniques for React 

### **Using React Error Boundaries** 



<!-- Start of picture text -->
class ErrorBoundary CC ent {<br>ructor(props) {<br>(props);<br>«state = { hasError: i<br>}<br>etDeriv stateFromError(error) {<br>return { hasError: ue<br>}<br>I entDid h(error, errorInfo) {<br>‘ (‘Error caught:', error, errorInfo);<br>}<br>ender() {<br>if ( .state.hasError) {<br>return <h1>Something went wrong.</h1>;<br>at<br>}<br>return this.props.children;<br>}<br>1<br>}<br><!-- End of picture text -->

- Catch and handle errors in component trees 

- Prevent entire app from crashing due to component errors 

### **Debugging State and Props** 

- Use React Developer Tools to inspect component state and props 

- Implement logging in lifecycle methods or hooks 

### **Performance Profiling** 

- Use React Profiler to identify performance bottlenecks 

- Analyze component render times and optimize as needed 



<!-- Start of picture text -->
SWIN<br>BUR<br>*NE-<br><!-- End of picture text -->

# Debugging Tools for FastAPI 

### **Uvicorn Debug Mode** 

- Run FastAPI with `--reload` flag for automatic reloading 

- Example: `uvicorn main:app --reload -- port 8000` 

### **FastAPI's Built-in Documentation** 

- Access interactive API documentation at `/docs` endpoint 

- Test API endpoints directly from the browser 

### **Python Debugger (pdb)** 

- Built-in Python debugging tool 

- Set breakpoints, step through code, inspect variables 

### **Logging in FastAPI** 

- Use Python's built-in `logging` module 

- • Configure log levels and formats 



<!-- Start of picture text -->
# Python Debugger<br>import pdb<br>app. (""/debug-example")<br>async def debug_example():<br>pdb. () # Debugger will pause here<br>result ()<br>return {"result": result}<br># Logging in FastAPI<br>import logging<br>logging. (Level=Logging. DEBUG)<br>logger = logging. (__name__)<br>app.get("/log—example")<br>async def log_example():<br>logger. ("This is a debug message")<br>logger. ("This is an info message")<br>logger. ("This is a warning message")<br>return {"message": "Check the logs"}<br><!-- End of picture text -->



<!-- Start of picture text -->
SWiN<br>BUR<br><!-- End of picture text -->

# Debugging Techniques for FastAPI 



<!-- Start of picture text -->
# Examp le f a global ex ptio land Le<br>n fastapi port FastAPI, Request<br>fastapi.responses import JSONResponse<br>app 0<br>app. ( )<br>request: Request, exc: ):<br>content={"message": f"An unexpected<br>error occurred: { (exc) }'}<br>)<br>f pydantic import BaseModel, validator<br>: User( yz<br>username<br>email<br>age:<br>(‘age’)<br>v < 18:<br>return Vv<br>import time<br>app. ("http")<br>async def ad (request: Request, call_next):<br>start_time = time. 19]<br>response wait (request)<br>process_time = time. Q start_time<br>response. headers ["X-Process—Time"] (process_time)<br>eturn response<br><!-- End of picture text -->

### **Exception Handling** 

- Use try-except blocks to catch and handle exceptions 

- - Implement global exception handlers for consistent error responses 

### **Request Validation Debugging** 

- Use Pydantic models for request body validation 

- - Implement custom validators for complex validation logic 

### **Middleware for Debugging** 

- Implement custom middleware for logging or debugging 

- - Track request/response cycles, execution time, etc. 



<!-- Start of picture text -->
SWiN<br>~NE=<br><!-- End of picture text -->

# Full Stack Debugging Strategies 

#### **End-to-End Testing** 

- Implement integration tests that cover both frontend and backend 

- Use tools like Cypress or Selenium for automated E2E testing 

#### **API Testing** 

- Use tools like Postman or Insomnia for API testing 

- Create and run automated API tests 

#### **Network Debugging** 

- Use browser Network tab to inspect API calls 

- • Monitor request/response cycles, headers, and payloads 

Image from [Eficode] 

#### **Cross-Origin Resource Sharing (CORS) Debugging** 

- Understand CORS errors and how to resolve them 



<!-- Start of picture text -->
BUR<br><!-- End of picture text -->

# Tools for Full Stack Development 

##### **Version Control Systems** 

- Git: Distributed version control system 

- GitHub/GitLab: Platforms for hosting and collaborating on Git repositories 

##### **Continuous Integration/Continuous Deployment (CI/CD) Tools** 

- Jenkins: Open-source automation server 

- GitLab CI: Integrated CI/CD platform 

- GitHub Actions: CI/CD platform integrated with GitHub 



<!-- Start of picture text -->
Image from [medium.com]<br>Jenkins<br><!-- End of picture text -->

Image from [learntek] 

##### **Monitoring and Logging Tools** 

- ELK Stack (Elasticsearch, Logstash, Kibana): For log management and analysis 

- Prometheus and Grafana: For metrics collection and visualization 

##### **Container and Orchestration Tools** 

Image from [medium.com] 

- Docker: Platform for containerizing applications 

- Kubernetes: Container orchestration platform for scaling and managing containerized applications 



- **Recap Front-end & Back-end** 

- **React API Call** 

- **Data Visualization** 

- **Full-stack integration** 

- **Debugging and Troubleshooting** 

- **Best Practices in Code Development** 



<!-- Start of picture text -->
d ‘<br>AZe $ a<br>Gee 2 _&<br>a?<br><!-- End of picture text -->

Image from [Pinterest] 



<!-- Start of picture text -->
BUR<br>*NE-<br><!-- End of picture text -->

# Code Development Best Practices 

**Why are following Best Practices Important?** 

   - Improve code quality and readability 

   - Enhance maintainability and scalability 

   - Reduce bugs and technical debt 

- Facilitate team collaboration and knowledge sharing 

- **Benefits of High-Quality Code** 

   - Faster development cycles 

   - Easier onboarding for new team members 

   - Reduced long-term costs 



- Improved software reliability and performance 

Image from [Pinterest] 



# Code Style and Consistency 

##### **Importance of Coding Standards** 

- Ensures uniform code appearance across the project 

- Reduces cognitive load when reading and reviewing code 

- Facilitates easier maintenance and updates 

##### **Popular Style Guides** 

- Python:  PEP 8 (Python Enhancement Proposal 8) 

- JavaScript/React:  Airbnb React/JSX Style Guide 

- General: Google Style Guides for various languages 

##### **Enforcing Code Style** 

- Use linters and formatters: 



<!-- Start of picture text -->
def ite V (numbers):<br>"""Calculate the average of a list of numbers."""<br>if numbers:<br>return (numbers) (numbers)<br># Bad<br>Jef rte ( numbers ):<br>if numbers: return 0<br>return (numbers) (numbers)<br><!-- End of picture text -->

Python: flake8, black 

JavaScript: ESLint, Prettier 

- Integrate with CI/CD pipeline for automated checks 



<!-- Start of picture text -->
SWIN<br>BUR<br>*NE-<br><!-- End of picture text -->

# Clear Code Structure 

##### **Importance of Clear Code Structure** 

- A **clear code structure** ensures consistency, making code easier to read, navigate, and maintain. It supports collaboration by helping team members understand the project quickly. Organized code simplifies debugging and allows for smoother scaling as the project grows. In short, it improves efficiency and reduces errors in development. 

##### **Good Code Structure Guides for React** 

- A typical React project should follow a well-organized structure that separates concerns and promotes reusability: 



<!-- Start of picture text -->
my-react-—app/<br>public/<br>L— index.html # Main HTML file<br>Src/<br>assets/ # Static assets like images, fonts, etc.<br>components/ # Reusable React components<br>services/ # API calls or business logic<br>hooks/ # Custom React hooks<br>pages/ # Different pages or views<br>styles/ # Global CSS or SASS files<br>App.js # Main App component<br>index.js # Entry point of the application<br>App.css # App-level styling<br>env # Environment variables<br>package.json # Project dependencies and scripts<br>README .md # Documentation<br><!-- End of picture text -->



<!-- Start of picture text -->
SWIN :<br>ae oe<br><!-- End of picture text -->

# Clear Code Structure 

##### **Good Code Structure Guides For FastAPI (python)** 

A well-structured FastAPI project encourages modularity and scalability. Here’s an ideal layout for a FastAPI project: 



<!-- Start of picture text -->
my_fastapi_project/<br>app/<br>api/ # API routes<br>v1i/<br>[Ee endpoints/ # API endpoints (e.g., auth, users, items)<br>__init__.py<br>__init__.py<br>core/ # Application settings, configuration, and security<br>models/ # Pydantic models for data validation or ORM models<br>services/ # Business logic, background jobs, external API calls<br>db/ # Database models and session management<br>utils/ # Utility functions<br>main.py # Entry point to start FastAPI app<br>__init__.py<br>tests/ # Unit and integration tests<br>-env # Environment variables<br>requirements.txt # Python dependencies<br>README .md # Documentation<br><!-- End of picture text -->



<!-- Start of picture text -->
SWIN<br>BUR dais<br><!-- End of picture text -->

# Version Control Best Practices 

### **Git Workflow** 

   1. Create a feature branch from main/master 

   2. Make small, focused commits 

   3. Pull and rebase regularly to stay up-to-date 

   4. Create a pull request for code review 

   5. Merge after approval and passing CI checks 

- **Meaningful Commit Messages** 

Image from [Pinterest] 

- Use the imperative mood: "Add feature" instead of "Added feature" 

- Provide context in the commit body 

- Reference issue numbers if applicable 

- Example: 



<!-- Start of picture text -->
feat: Add user authentication system<br>Implement JWT-based authentication<br>Create login and registration endpoints<br>Add middleware for protected routes<br>Closes #issue123<br><!-- End of picture text -->



<!-- Start of picture text -->
SWIN<br>BUR<br>*NE-<br><!-- End of picture text -->

# Code Comments and Documentation 



<!-- Start of picture text -->
# Inline Documentation<br>Jef (price: , percentage: )-> :<br>if i) percentage 100:<br>return price * (1 — percentage / 100)<br><!-- End of picture text -->

**When and How to Write Comments** 

- Explain "why" rather than "what" the code does 

- Use comments for complex algorithms or business logic 

- Keep comments up-to-date with code changes 

**Types of Documentation** 

1. Inline Documentation 

Docstrings for functions, classes, and modules 

2. README Files 

Project overview, setup instructions, and usage examples 

Badges for build status, code coverage, etc. 

3. API Documentation 

Use tools like Swagger/OpenAPI for RESTful APIs 

Provide examples and expected responses 

4. Architecture and Design Documents 

High-level system design and component interactions 



<!-- Start of picture text -->
SWIN<br>BUR<br>*NE-<br><!-- End of picture text -->

Data flow diagrams and entity-relationship diagramslanguages 

# Code Complexity Management 

##### **Keeping Functions and Methods Simple** 

- Follow the Single Responsibility Principle (SRP) 

- Aim for functions under 20-30 lines of code 

- Use descriptive names to selfdocument code 

##### **Avoiding Code Duplication (DRY Principle)** 

- Extract common functionality into reusable functions or classes 

- Use inheritance and composition effectively in object-oriented programming 

- Implement utility functions for frequently used operations 



<!-- Start of picture text -->
(aneaieY<br>Rite7 cites U data:<br>item['sta ] 3<br>item['type'] user’:<br>result (<br>item[ ]<br>renee:<br>»<br>item['type'] n’s<br>result. ({<br>item[ 1,<br>me’: item[ me }<br>») . a<br>result<br><!-- End of picture text -->



<!-- Start of picture text -->
/ (item):<br>return item[‘status'] active<br>return {<br>id': item['id'],<br>name’: item['name'],<br>emai item['email']<br>}<br>jef (item):<br>n{<br>i': item['id'],<br>name': item['name'],<br>e°: ‘administrator<br>}<br>jef (data):<br>processors = {<br>user’: process_user,<br>admir process_admin<br>}<br>turn [processors [item['type']] (item)<br>item data if (item)]<br><!-- End of picture text -->



<!-- Start of picture text -->
SWIN<br>BUR<br>*NE-<br><!-- End of picture text -->

# Code 

#### **Importance of Code Review** 

- Improves overall code quality 

- Catches bugs and security issues early 

- Shares knowledge across the team 

- Ensures adherence to coding standards and best practices 

#### **Effective Code Review Techniques** 

- Use a checklist to ensure consistency 

- Focus on the architecture and design first, then details 

- Provide constructive feedback with explanations 

Image from [pinterest] 

- Use automated tools to catch style issues before human review 

- Keep reviews small and frequent (under 400 lines of code per review) 



# Code Review 

#### **Code Review Checklist** 

- Does the code follow the project's style guide? 

- Is the code well-documented and easy to understand? 

- Are there any potential security vulnerabilities? 

- Is the code efficient and performant? 

- Are edge cases handled properly? 

- Are there appropriate unit tests? 



<!-- Start of picture text -->
Example Code Review Comment:<br>In the ‘process_payment* function:<br>Consider using a decimal type instead of for currency<br>calculations to avoid precision issues. Also, it might be good<br>to add a check for negative amounts to prevent invalid payments.<br>Suggested change:<br>from decimal port Decimal<br>def (amount: Decimal):<br>if amount ('0'):<br># Restaisef the funct Me"Payment; amount must be positivea<br>ee pe NEE at CL<br><!-- End of picture text -->



<!-- Start of picture text -->
SWiN<br>BUR<br>*NE-<br><!-- End of picture text -->

# Code Refactoring 

##### **Identifying Refactoring Opportunities** 

- Code smells (e.g., duplicate code, long methods, large classes) 

- Declining performance 

- Difficulty in adding new features 

- Increasing technical debt 

##### **Common Refactoring Techniques** 

- Extract Method: Break down long methods into smaller, focused ones 

- Rename: Improve naming of variables, methods, and classes 

- Move Method: Relocate methods to more appropriate classes 

- Replace Conditional with Polymorphism: Use polymorphism instead of complex conditionals 

- • Introduce Parameter Object: Group related parameters into a single object 



<!-- Start of picture text -->
function (items) {<br>let total = 0;<br>for (let i = 0; i < items. length; i++) {<br>total items[i].price « items[i] . quantity;<br>if (items[i] .type food') {<br>total @.9; // 10% discount on food items<br>}<br>}<br>return total;<br>}<br>// After refactoring<br>return items. ((total, item) => total<br>(item), ®);<br>}<br>const baseTotal item.price item. quantity;<br>returr (baseTotal, item.type);<br>}<br>function (total, itemType) {<br>} return itemType food total * 0.9 : total;<br><!-- End of picture text -->



<!-- Start of picture text -->
BUR<br>*NE-<br><!-- End of picture text -->



<!-- Start of picture text -->
SW N SWINBURNE<br>B U R UNIVERSITY OF<br>“NE: TECHNOLOGY<br><!-- End of picture text -->

Thank you 

