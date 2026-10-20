



COS30049 – Computing Technology Innovation Project Week 11 – Building a Full-Stack Application 

( Lecture – 01 ) 

Ningran Li (Icey) <u>ningranli@swin.edu.au</u> 





## Acknowledgement of Country 

We respectfully acknowledge the Wurundjeri People of the Kulin Nation, who are the Traditional Owners of the land on which Swinburne’s Australian campuses are located in Melbourne’s east and outer-east, and pay our respect to their Elders past, present and emerging. 

We are honoured to recognise our connection to Wurundjeri Country, history, culture, and spirituality through these locations, and strive to ensure that we operate in a manner that respects and honours the Elders and Ancestors of these lands. 

We also respectfully acknowledge Swinburne’s Aboriginal and Torres Strait Islander staff, students, alumni, partners and visitors. 

We also acknowledge and respect the Traditional Owners of lands across Australia, their Elders, Ancestors, cultures, and heritage, and recognise the continuing sovereignties of all Aboriginal and Torres Strait Islander Nations. 





<!-- Start of picture text -->
2 ia *]<br>Y i, ‘ ry)<br><!-- End of picture text -->



<!-- Start of picture text -->
I I 1 1 I 1 1 1 I I I 1 i<br><!-- End of picture text -->

- **Recap Front-end & Back-end** 

- • **React API Call** 

- **Data Visualization** 

- **Full-stack integration** 

- • **Debugging and Troubleshooting** • **Best Practices in Code Development** 



<!-- Start of picture text -->
d<br>- (CWA A.<br>0a g<br>tz Za 7 ”<br>a<br><!-- End of picture text -->

Image from [Pinterest] 



<!-- Start of picture text -->
BUR<br>*NE-<br><!-- End of picture text -->



<!-- Start of picture text -->
Co,<br>° . . ‘<br>. . . ,<br>: . ‘ .<br><!-- End of picture text -->

# React Lifecycle 



<!-- Start of picture text -->
Initialization Mounting Updation Unmounting<br>For Props For State<br>getDerivedStateFromProps() i setState()<br>shouldComponentUpdate()<br>Set Props and render()<br>Initial State of<br>inthfenert getSnapshotBeforeUpdate() ComponentWillUnmount().<br>componentDidMount()<br>render()<br>React Methods Oo ComponentDidUpdate()<br>ReactDOM Methods 0 0G<br><!-- End of picture text -->



<!-- Start of picture text -->
BUR<br><!-- End of picture text -->

Image from [GFG] ~~—~~ 

# FastAPI 

### **What is FastAPI?** 

- Modern, fast (high-performance) web framework for building APIs with Python 3.6+ 

- Based on Starlette and Pydantic 

### **Key Features** 

Fast to code `｜` Fewer bugs `｜` Intuitive `｜` Easy to use and learn 

### **Basic Operations** 

- Path Operations: Define API endpoints using decorators 

- Query Parameters: Automatically parsed from the URL 

- Request Body: Use Pydantic models to declare the structure of request bodies 



<!-- Start of picture text -->
from fastapi import FastAPI<br>from pydantic import BaseModel<br>app Q<br>class Item(BaseModel):<br>name:<br>price:<br># Path Operation<br>@app.get("/items/{item_id}")<br>async def read_item(item_id: ye<br>return {"item_id": item_id}<br># Query Parameters<br>@app. ("/items/")<br>async def read_items(skip: Q, limit: 10):<br># parsed from the URL's query string,<br>#e.g., /items/?skip=0&limit=10.<br>return {"skip": skip, "limit": limit}<br># Request Body<br>@app. ("/items/")<br>async def creat tem(item: Item):<br>return item<br><!-- End of picture text -->



<!-- Start of picture text -->
SWIN<br>BUR<br>*NE-<br><!-- End of picture text -->

- **Recap Front-end & Back-end** 

- • **React API Call** 

- **Data Visualization** 

- **Full-stack integration** 

- **Debugging and Troubleshooting** 

- • **Best Practices in Code Development** 



<!-- Start of picture text -->
d<br>- (CWA A.<br>0a g<br>tz Za 7 ”<br>a<br><!-- End of picture text -->

Image from [Pinterest] 



<!-- Start of picture text -->
BUR<br>*NE-<br><!-- End of picture text -->

# Frontend API Calls vs Backend API Interfaces 



<!-- Start of picture text -->
Frontend Backend<br>Browser Initiates API call Ssends request to——_,] Processes requestLEA<br>API Calls API Server<br>Updates frontend UI Returns response to Returns response data<br><!-- End of picture text -->

##### **Location** 

##### **Purpose** 

- Frontend API Call: Client-side (Browser) 

   - Frontend: Requests data/services 

- Backend API Interface: Server-side 

- Backend: Processes requests, returns responses 

##### **Language** 

##### **Relationship** 

- Frontend: JavaScript/TypeScript 

   - Frontend initiates communication 

- Backend: Python, Java, etc. 

- Backend responds with data/results 

##### **Analogy: Restaurant Order System** 

- They work together to create a complete application 



<!-- Start of picture text -->
Restaurant Scene Order Processing Flow<br>Places Order. Sends Order: Processes Order.<br>Customer (Browser) Waiter (API Call) Order (API) ey Kitchen (Server)<br>‘Serves Dish Food Prepares & Sends Back<br><!-- End of picture text -->



<!-- Start of picture text -->
SWiIN<br>BUR :<br>. N E .<br><!-- End of picture text -->

# Make React API Calls (XMLHttpRequest) 

###### **_1. useState Hook_** 

- Initializes a state variable data with a default value of null and provides a function setData to update the value of data 

- The useState hook is used to handle state within functional 1 

- components in React 

###### **_2. handleClick Function_** 

- This function is triggered when the user clicks a button (defined in 3) 

- an XMLHttpRequest object (xhr) is created to make an HTTP request to the API endpoint <u>https://api.example.com/data</u> 2 

- xhr.open('GET', ...) sets up the request method (GET) and the target URL 

- The xhr.onload callback is triggered when the request is complete 

- • If the request is successful (status 200), it parses the received JSON response (xhr.responseText) and updates the data state using setData 

   - xhr.send() sends the request to the server. 

- 

###### **_3. JSX (UI Rendering)_** 

- This part of the code defines what will be rendered on the screen. 

- • This part of the code defines what will be rendered on the screen. 

- • The code also conditionally renders the response data 3 

- If data is not null, it displays the data inside a <div>. The data is converted to a string using JSON.stringify(data) 

- If data is still null (i.e., before the data is fetched), it shows a "Loading..." message instead 



<!-- Start of picture text -->
React, { useState } ‘react';<br>Example() {<br>[data, setData] = useState(null);<br>handleClick() {<br>xhr = XMLHttpRequest ();<br>xhr.open('GET', 'https://api.example.com/data');<br>xhr.onload = () {<br>(xhr.status === 200) {<br>setData(JSON.parse(xhr.responseText) );<br>}<br>}<br>i;<br>xhr.send();<br>i<br>I<br>(<br><div><br><button onClick={handleClick}>Get Data</button><br>{data ? <div>{JSON.stringify(data)}</div> : <div>Loading...</div>}<br></div><br>yy<br>}<br><!-- End of picture text -->

# Make React API Calls (Fetch API) 

##### **_1. useState Hook_** 

##### **_2. useEffect Hook_** 

1 

- a React hook that performs side effects in functional components, like fetching data 

- The fetch function is used to make a GET request to https://api.example.com/data 

- When the response is received, it's converted into JSON format using response.json() 

   - 2 

- After parsing the JSON, the result is passed to setData, which updates the data state 

- The empty array [] as the second argument to useEffect ensures that this effect runs only once, when the component mounts, mimicking the behavior of componentDidMount in class-based components 

- If an error occurs during fetching, it is caught by the 3 

- catch block, which logs the error to the console. 

##### **_3. JSX (UI Rendering)_** 



<!-- Start of picture text -->
React, { useState, useEffect } "react';<br>App() {<br>[data, setData] = useState(null);<br>useEffect(() => {<br>fetch( ‘https://api.example.com/data')<br>. then(response => response. json())<br>.then(json => setData(json))<br>»catch(error => -error(error));<br>}, ();<br>(<br><div><br>{data ? <pre>{JSON.stringify(data, null, 2)}</pre> : 'Loading...'}<br></div><br>i;<br>at<br>£<br>App;<br><!-- End of picture text -->

# Make React API Calls (Axios) 

###### **_1. useState Hook_** 

   - 1 

- posts is a state variable initialized as an empty array. It will store the list of posts retrieved from the API 

- setPosts is a function used to update the state when the posts are fetched 

###### **_2. useEffect Hook_** 

2 

- The useEffect hook is used to run side effects, like fetching data, after the component has been rendered 

- Inside useEffect, an axios.get request is made to the https://jsonplaceholder.typicode.com/posts API to retrieve posts 

- axios.get returns a Promise which, upon resolution, contains the API response. The .then() method processes this response 

- response.data contains the array of posts from the API, which is passed to setPosts to update the state 

- If there's an error during the request, it’s caught by the .catch() method, and the error is logged to the console 

- The empty dependency array [] ensures this effect only runs once, mimicking the behavior of componentDidMount in class components. 

3 

###### **_3. JSX (UI Rendering)_** 

- The component renders an unordered list (<ul>) 

- Inside the list, posts.map() is used to iterate over each post from the posts array 

- For each post, a list item (<li>) is created displaying the post.title. The key attribute is set to post.id, ensuring each list item has a unique identifier (important for React's rendering optimization) 



<!-- Start of picture text -->
React, { useState, useEffect } ‘react';<br>axios ‘axios';<br>App() {<br>[posts, setPosts] = useState([]);<br>useEffect(() => {<br>axios.get('https://jsonplaceholder.typicode.com/posts')<br>.then(response => {<br>setPosts(response.data);<br>})<br>-catch(error => {<br>-error(error);<br>b);<br>y, 11);<br>(<br><ul><br>{posts.map(post => (<br><li key={post.id}>{post.title}</li><br>))}<br></ul><br>i<br>}<br>App;<br><!-- End of picture text -->

# Make React API Calls (Key Differences) 

### **XMLHttpRequest:** 

- An older API that is callback-based and has verbose syntax. It supports older browsers but requires manual handling for most tasks. 

### **Fetch API:** 

- A modern, Promise-based API that is simpler to use but lacks progress monitoring and requires additional handling for features like timeouts. 

- **Axios:** 

- A Promise-based library that simplifies HTTP requests with built-in features like JSON handling and request timeouts. Requires installation but provides more advanced features out of the box. 



Let‘s continue learning and mastering the skills in workshop! 



- **Recap Front-end & Back-end** 

- • **React API Call** 

- **Data Visualization** 

- **Full-stack integration** 

- • **Debugging and Troubleshooting** • **Best Practices in Code Development** 



<!-- Start of picture text -->
d<br>- (CWA A.<br>0a g<br>tz Za 7 ”<br>a<br><!-- End of picture text -->

Image from [Pinterest] 



<!-- Start of picture text -->
BUR<br>*NE-<br><!-- End of picture text -->

# Three I’s of Data Visualization 

**1. Interactivity:** The visualization should allow users to explore and interact with the data, such as filtering, zooming, or adjusting parameters to uncover deeper insights. 

**2. Information** : The data should be presented clearly and accurately, allowing the viewer to understand the insights and story behind the data. 

**3. Interpretation:** The visual should help the audience easily interpret and draw meaningful conclusions from the data, making complex information more accessible and actionable. 



<!-- Start of picture text -->
Three I's of Data Visualization<br>Interactivity &<br>|<br>Intuitiveness<br>/<br>.<br>Informativeness ©<br><!-- End of picture text -->

Image from [kellton] 



<!-- Start of picture text -->
BUR se<br>. NE .<br><!-- End of picture text -->





<!-- Start of picture text -->
a "e@o* ‘entsanes! uae et<br>ope ge So 5=e@oe=--< Ta <\ =<br>i PI ey ta@esee rete<br>Ve —~ > pea, a<br>i y, PMasspi™ / (_ ss ae : We Mie bed ol x \.<br>op = (_\\\ iN -<br>» prose NX a el iy i ee<br>~<br>see 7 fm. P= Sue = —<br>;Sac ae = Zé = = 5 | aa Eze<br>ayForce Seletg i, eel ca — re ee=<br>= . wo re.af a ,| raeeee<br>YZ emme i i.e s _ 4 oon =<br><!-- End of picture text -->

Introduction of D3.js 

# Usage of D3.js 

**D3.js** `：` **Bar Chart** 

### **npm install d3** 



<!-- Start of picture text -->
import React, {Component} from 'react';<br>// import your d3 library here<br>// to install ds by : npm install d3<br>import * as d3 from "d3";<br>// This is the basic template for the d3 chart<br>class SampleChart extends Component {<br>}<br>export default SampleChart;<br><!-- End of picture text -->



<!-- Start of picture text -->
BUR<br>*NE-<br><!-- End of picture text -->

# Usage of D3.js 

In order to display the bar chart whenthe sampleChart component is mounted to the DOM, we will utilize the ComponentDidMount lifecycle. 

In D3.js, loading the visualization logic within the **ComponentDidMount** lifecycle method is a common practice in React applications. 



<!-- Start of picture text -->
: : 1 ; : 1 ; :<br>: \ \ ; : \<br><!-- End of picture text -->



<!-- Start of picture text -->
import React, { Component } from ‘react'<br>import * as d3 from ‘'d3'<br>class sampleChart extends Component {<br>componentDidMount() {<br>+<br>generateChart() {<br>const data = [10, 5, 7, 8, 2, 8];<br>const svg = d3.select("body")<br>. append("svg")<br>-attr("“width", 1200)<br>-attr("height", 400);<br>svg.selectAll("rect")<br>.data(data)<br>-enter()<br>. append("rect")<br>sattr("x", (d, i) => i * 70)<br>-attr("y", (d, i) => 300 — 10 x d)<br>-attr("width", 65)<br>-attr("height", (d, i) => d * 10)<br>sattr(“fTill",. “green");<br>Jp<br>render() {<br>return <div ></div><br>i<br>evnart default camnleChart:<br><!-- End of picture text -->



<!-- Start of picture text -->
BUR<br>*NE-<br><!-- End of picture text -->

# Usage of D3.js 

**_<u>generateChart()</u>_** is the method we use to create ~~—~~ D3.js charts. In React, this step is crucial as it ensures that the chart is only displayedwhen the component is mounted to the DOM. 

Firstly, we define a parameter whichcontains the data for the chart we want to visualise. Next, we define an image in **SVG** format using the D3.js method. SVGis usedbecause it is scalable and the data will not appear pixelated regardless of how the screen size is scaled or broadened. 



<!-- Start of picture text -->
7 ' ' ' 7 ' ' 7<br>' ' ' ' ' ' ' '<br><!-- End of picture text -->



<!-- Start of picture text -->
import React, { Component } from ‘react'<br>import * as d3 from ‘'d3'<br>class sampleChart extends Component {<br>componentDidMount() {<br>this.generateChart();<br>generateChart() {<br>const data = [10, 5, 7, 8, 2, 8];<br>const svg = d3.select("body")<br>-append("svg")<br>-attr("width", 1200)<br>-attr("height", 400);<br>svg.selectAll("rect")<br>.data(data)<br>.enter()<br>.append("rect")<br>sattr("x", (d, i) => i * 70)<br>sattr("y", (d, i) => 300 - 10 * d)<br>sattr("width", 65)<br>sattr("height", (d, i) => d * 10)<br>sattr("fill", "green");<br>}<br>render() {<br>return <div ></div><br>hp<br>eavnart default camnleChart:<br><!-- End of picture text -->



<!-- Start of picture text -->
*NE-<br>BUR<br><!-- End of picture text -->

# Usage of D3.js 

The **_d3.select()_** method selects an HTML element. It selects the first element that matchesthe passedparameter and creates a node for it. Here we have passed the body element. 

The **_attr()_** method is responsible for adding attributes tothe element, which can be any attribute of the HTML element, such as class, height, width, etc. 



<!-- Start of picture text -->
. . ' ‘ . ' ‘ .<br>' ' ' ' ' ' ' '<br><!-- End of picture text -->



<!-- Start of picture text -->
import React, { Component } from ‘react'<br>import * as d3 from ‘'d3'<br>class sampleChart extends Component {<br>componentDidMount() {<br>this.generateChart();<br>generateChart() {<br>const data = [10, 5, 7, 8, 2, 8];<br>const svg = d3.select("body")<br>-append("svg")<br>sattr("width", 1200)<br>-attr("height", 400);<br>svg.selectAll("rect")<br>.data(data)<br>.enter()<br>.append("rect")<br>sattr("x", (d, i) => i * 70)<br>sattr("y", (d, i) => 300 - 10 * d)<br>sattr("width", 65)<br>sattr("height", (d, i) => d * 10)<br>eattr("fill", "green");<br>}<br>render() {<br>return <div ></div><br>hp<br>eavnart default camnleChart:<br><!-- End of picture text -->



<!-- Start of picture text -->
*NE-<br>BUR<br><!-- End of picture text -->

# Usage of D3.js 

**.selectAll("rect")** selectsall rectangular elements in the SVG. 

**.data(data)** bindsthe data to the selected rectangle element. 

**.attr("x", (d, i) => i * 70)** : herethe x-coordinate of the rectangles is set, and the x-coordinateinterval ofeach rectangle is set to 70, according to the index i of the data in the array y<svg width="1200" height="400"> 



<!-- Start of picture text -->
—<br><!-- End of picture text -->



<!-- Start of picture text -->
import React, { Component } from ‘react'<br>import * as d3 from ‘d3'<br>class sampleChart extends Component {<br>componentDidMount() {<br>this.generateChart();<br>a<br>generateChart() {<br>const data = [10, 5, 7, 8, 2, 8];<br>const svg = d3.select("body")<br>-append("svg")<br>-attr("width", 1200)<br>-attr("height", 400);<br>svg.selectAll("rect")<br>.data(data)<br>-enter()<br>-append("rect")<br>sattr("x", (d, i) => i + 70)<br>.<br>-attr("y", (d, i) => 300 - 10 *d<br>.attr("width", 65)<br>.attr("height", (d, i) => d * 10)<br>-attr("fill", "“green");<br>}<br>render() {<br>return <div ></div><br>ip<br>avnart© defaul+ camnleChart-:<br><!-- End of picture text -->



<!-- Start of picture text -->
SWIN<br><!-- End of picture text -->

# Usage of D3.js 

**.attr("width",65):** sets the width of the rectangle to a fixed value 65 

**.attr("height", (d, i) => d * 10):** set the height of the rectangle, according to the data d, set the height ofthe rectangle to 10 times the data value d 

**.attr("fill", "green")** : set the fill colour of the rectangle to green 

y<svg width="1200" height="400"> 



<!-- Start of picture text -->
—<br><!-- End of picture text -->



<!-- Start of picture text -->
import React, { Component } from ‘react'<br>import * as d3 from ‘d3'<br>class sampleChart extends Component {<br>componentDidMount() {<br>this.generateChart();<br>a<br>generateChart() {<br>const data = [10, 5, 7, 8, 2, 8];<br>const svg = d3.select("body")<br>-append("svg")<br>-attr("width", 1200)<br>-attr("height", 400);<br>svg.selectAll("rect")<br>.data(data)<br>-enter()<br>-append("rect")<br>sattr("x", (d, i) => i + 70)<br>.<br>-attr("y", (d, i) => 300 - 10 *d<br>.attr("width", 65)<br>.attr("height", (d, i) => d * 10)<br>-attr("fill", "“green");<br>}<br>render() {<br>return <div ></div><br>ip<br>avnart© defaul+ camnleChart-:<br><!-- End of picture text -->



<!-- Start of picture text -->
SWIN<br><!-- End of picture text -->



<!-- Start of picture text -->
Bar chart Horizontal bar chart Diverging bar chart Stacked bar chart Stacked horizontal bar chart Stacked normalized horizon...<br>ala ! — — sy) (us SA TY ampetiratal:<br>Grouped bar chart Diverging stacked bar chart Marimekko chart World history timeline Calendar The impact of vaccines<br>= ===a—<br>a=<br>I aa zi ei<br>Electricity:  usage,=.= 2019-- Revenue by music format, 1... ‘Theaewealth & health of natio . . Scatterplot touree Bar chart race Treemap CascadedPeer  treemapaPees= (| PENested<br><!-- End of picture text -->



<!-- Start of picture text -->
BUR<br><!-- End of picture text -->

More Charts of D3.js 

# Introduction of Chart.js 

Chart.js provides a set of frequently used chart types, plugins, and customization options. In addition to a reasonable set of <u>built-in chart types</u> ~~SEEN~~ 



<!-- Start of picture text -->
Line Chart HD Senwary MORO Feoruay EE March EME Ape ANC May WOE une WEE July<br>48 Hy Fst czas 660=<br>* GOOGg Poets<br>SESSOS 5<br>8 SCS) Ye,<br>» BSCoeSOC0 ote%e%ee585 > yayate)<br>282a SOOOSOOOSOOO,<a4 maaieeeSata)a maTatt<br>SOoeoCoeSOOOOOSoe <aa at<br>15 Ae we mma<br>0°00SSSI%e tet eZarereLL aaoai)<br>1» SOOOEOC ULOe ee2<br>SESC5C97 fe eh<br>5 SOO A ie)<br>Oot Cae ee<br>Januarya Febuay March pi May dune duly SOOSEatteAtteees "eeeeaten eeay<br>ee<br>Line Chart ME uy Fist dataset<br>ME by First dataset My second dataset ne<br>45 40<br>4 *<br>8<br>e . 3520<br>jalxo | 2%<br>20 “ 20<br>1s} 15<br>10 10<br>: : I<br>bs 5 0 | —<br>1 2 3 4 5 6 7 January Febuary Mareh Api May June duly<br><!-- End of picture text -->



<!-- Start of picture text -->
SWINTHT<br>BUR<br><!-- End of picture text -->

Usage of Chart.js 



<!-- Start of picture text -->
// <block: config: 0><br>const config = {<br>type: ‘'bar',<br>data: data,<br>options: {<br>scales: {<br>y: {<br>beginAtZero: true<br>}<br>} ,<br><!-- End of picture text -->



<!-- Start of picture text -->
sy rust Dataset<br>90<br>80<br>70<br>60<br>50<br>o<br>7<br>“<br>10<br><!-- End of picture text -->



<!-- Start of picture text -->
*NE-<br><!-- End of picture text -->

# , , , , , , , , Usage of Chart.js 



<!-- Start of picture text -->
// <block:setup:1><br>const labels = Utils.months({count: 7});<br>const data = {<br>labels: labels,<br>datasets: [{<br>label: 'My First Dataset',<br>data: [65, 59, 80, 81, 56, 55, 40],<br>backgroundColor: [<br>‘rgba(255, 99, 132, @.2)',<br>"rgba(255, 159, 64, @.2)',<br>‘rgba(255, 205, 86, @.2)',<br>‘rgba(75, 192, 192, @.2)',<br>‘rgba(54, 162, 235, @.2)',<br>‘rgba(153, 102, 255, @.2)',<br>"rgba(201, 203, 207, 0.2)'<br>1,<br>borderColor: [<br>‘rgb(255, 99, 132)',<br>"rgb(255, 159, 64)',<br>‘rgb(255, 205, 86)',<br>'rgb(75, 192, 192)',<br>"rgb(54, 162, 235)',<br>‘rgb(153, 102, 255)',<br>'rgb(201, 203, 207)'<br>1,<br>borderWidth: 1<br>"<br>}<br>'<br><!-- End of picture text -->

#### **Const data = { … }:** 

#### **data: [65,59,80,81,56,55,40]:** 



<!-- Start of picture text -->
co My Rist Deteset<br>eo<br>-<br>70<br>so<br>0<br>40<br>.<br>~<br>20<br>°<br>0<br>January February March Apri Ma June july<br><!-- End of picture text -->



<!-- Start of picture text -->
BUR | gauane<br>»NE*<br><!-- End of picture text -->

# Usage of Chart.js 



<!-- Start of picture text -->
config = {<br>type: ‘doughnut',<br>data: data,<br><!-- End of picture text -->

Config object specifies the type of chart you want to create 



<!-- Start of picture text -->
a<br><!-- End of picture text -->



<!-- Start of picture text -->
BUR<br>. N E .<br><!-- End of picture text -->

Usage of Chart.js 



<!-- Start of picture text -->
// <block:setup:1><br>const data = {<br>labels: [<br>"Red',<br>"Blue',<br>"Yellow'<br>1,<br>datasets: [{<br>label: 'My First Dataset',<br>data: [300, 50, 100],<br>backgroundColor: [<br>Urgb (255,99, 132)07<br>"rgb(54, 162, 235)',<br>"rgb(255, 205, 86)'<br>1,<br>hoverOffset: 4<br>}]<br>i<br>// </block: setup><br>// <block: config: ><br>const config = {<br>type: 'doughnut',<br>data: data,<br>i<br>// </block: config><br>module.exports = {<br>actions: [],<br>config: config,<br>ti<br><!-- End of picture text -->





<!-- Start of picture text -->
-NE° fee<br><!-- End of picture text -->

- **Recap Front-end & Back-end** 

- **React API Call** 

- **Data Visualization** 

- **Full-stack integration** 

- • **Debugging and Troubleshooting** • **Best Practices in Code Development** 



<!-- Start of picture text -->
d<br>- (CWA A.<br>0a g<br>tz Za 7 ”<br>a<br><!-- End of picture text -->

Image from [Pinterest] 



<!-- Start of picture text -->
BUR<br>*NE-<br><!-- End of picture text -->



<!-- Start of picture text -->
Front-end (React)<br>State React User<br>Management Components Interface Al Model<br>Pre-Trained<br>Model<br>Data Visualization Model<br>Packaging<br>Recharts / D3.js _> API Calls<br>HTTP.<br>Requests<br>ie aa Back-end (FastAPI)<br>Responses<br>FastAPI Server —————> API Endpoints —————> Data Processing ————> rer<br>Po<br><!-- End of picture text -->



<!-- Start of picture text -->
BUR<br>*NE-<br><!-- End of picture text -->

Architecture Diagram 

# Architecture Overview 

#### **Full-stack Architecture with AI Integration** 

   - React (Frontend): Handles UI, user interactions, and data visualization 

   - FastAPI (Backend): Manages API endpoints, data processing, and AI model integration 

- Packaged AI Model: Pre-trained model integrated into the backend for real-time predictions or analysis 

- **Communication Flow** 

   - User interacts with React frontend 

   - React sends HTTP requests to FastAPI backend 

   - FastAPI processes requests, interacts with the AI model 

   - Backend sends responses back to React 

   - React updates UI and visualizes data based on responses 

#### **AI Model Integration** 

- AI model is packaged as a Python module 

- Backend imports and utilizes the AI model for data processing or predictions 

- Results are sent back to the frontend for visualization 



<!-- Start of picture text -->
SWIN<br>BUR |e<br>*NE-<br><!-- End of picture text -->

# Setting Up the Development Environment 

#### **React Setup** 

- Create React App: `npx create-react-app my-app` 

- Key dependencies: `axios` for API calls 

#### **FastAPI Setup** 

- Virtual environment `｜` Install FastAPI 

- CORS middleware for allowing cross-origin requests 

#### **AI Model Integration** 



<!-- Start of picture text -->
y ——\<br>ayyLAL) Backend<br>ee<br>t<br><!-- End of picture text -->

Image from [Pinterest] 

- Package pre-trained AI model as a Python module 

- Install the AI model package in the FastAPI environment 

#### **Development Servers on Local Host** 

- React: `npm start` (usually on localhost:3000) 

- FastAPI: `uvicorn main:app --reload` (usually on localhost:8000) 



# Method 1 - Packaging AI Models for Integration 

#### **Creating a Python Package** 

- Structure the AI model code 

- Create `setup.py` file 

- Use `__init__.py` to define public interface 

#### **Example Package Structure** 

#### **Basic setup.py Example** 

- Defining Metadata 

- Package Discovery 

- Specifying Dependencies 



<!-- Start of picture text -->
# Example Package Structure<br>my_ai_model/<br>__init__.py<br>model.py<br>utils.py<br>data/<br>L— pretrained_weights.pkl<br>setup.py<br># Basic setup.py Example<br>from setuptools import setup, find_packages<br>(<br>name="my_ai_model",<br>version="0.1",<br>description="An AI model package for marketing predictions",<br>packages Q,<br>install_requires=[<br>"pandas",<br>"scikit-learn",<br>ies<br>)<br># Making the Model Callable<br># In model.py<br>class MyAIModel:<br>def (self):<br># Load pretrained weights<br>pass<br>def edict(self, input_data):<br># Make predictions<br>return results<br><!-- End of picture text -->

#### **Making the Model Callable** 



<!-- Start of picture text -->
SWIN<br>BUR :<br>. NE .<br><!-- End of picture text -->

# Method 2 – AI Models Integration by Joblib 



<!-- Start of picture text -->
Y backend from fastapi import FastAPI,HTTPException<br>> __pycache__ from fastapi.middleware.cors import CORSMidd<br>from model import SimpleModel<br>5 :<br>© main.py from pydantic import BaseModel, Field<br>@ model.py from utils import logger<br>= simple_model.pkl<br><!-- End of picture text -->



### **Simpler joblib Integration** : 

- Use this for quick integrations, smaller projects, and when you don’t need to distribute the model as a Python package. 

Let‘s continue learning and mastering the skills in workshop! 



<!-- Start of picture text -->
BUR ees<br><!-- End of picture text -->

# Integrating AI Model with FastAPI 

**Installing the AI Model Package** pip install -e path/to/my_ai_model **Using the Model in FastAPI** 



<!-- Start of picture text -->
from fastapi import FastAPI<br>from my_ai_model import MyAIModel<br>app = | ()<br>model ()<br>@app. ("/predict")<br>async def predict(data: d ):<br>result = model. (data['input'])<br>return {"prediction": result}<br><!-- End of picture text -->



<!-- Start of picture text -->
BUR<br>*NE-<br><!-- End of picture text -->

# Implementing API Endpoints for AI Functionality 

### **Prediction Endpoint** 

**Model Information Endpoint** 

**Error Handling** Implement try-except blocks for robust error management 



<!-- Start of picture text -->
from fastapi import FastAPI<br>from my_ai_model import MyAIModel<br>app Q<br>model 10)<br># Prediction Endpoint<br>japp. ("/api/predict")<br>async def predict(data: PredictionRequest):<br>try:<br>result = model. (data. input)<br>return {"prediction": result}<br>except as e:<br>raise (status_code=400, detail=f"\<br>Invalid input: {str(e)}")<br>except as e:<br>raise (status_code=500, detail: (e))<br># Model Information Endpoint<br>japp. get ("/api/model-info")<br>async def model_info():<br>try:<br>return {<br>name": model.name,<br>version": model.version,<br>description": model.description<br>+<br>except as e:<br>raise (status_code=500, detail=f"\<br>Error retrieving model info: {str(e)}")<br><!-- End of picture text -->



<!-- Start of picture text -->
SWiN<br>*NE-<br><!-- End of picture text -->

# Using Axios in React for API Calls 

#### **What is Axios?** 

- Promise-based HTTP client for browser and Node.js 

- Simplifies making HTTP requests from JS 

#### **Key Features** 

- Automatic transforms for JSON data 

- Client-side protection against XSRF 

- Easy to use API 

#### **Installation** 

- npm install axios 

**Basic GET Request** 

#### **POST Request for Predictions** 



<!-- Start of picture text -->
import axios;<br>// Basic GET Request<br>const fetchData = async () => {<br>try {<br>const response = await axios. (‘http://localhost:\<br>8000/api/model-info');<br>} catch (error). Log(response.{ data) ;<br>. (‘Error fetching model info:', error);<br>+<br>Lee<br>// POST Request for Predictions<br>const makePrediction = async (inputData) => {<br>try {<br>const response = await axios. (‘http://localhost:\<br>8000/api/predict', {<br>input: inputData<br>});<br>(response. data.prediction) ;<br>} catch (error) {<br>: (‘Error making prediction:', error)<br>}<br>Le<br><!-- End of picture text -->



<!-- Start of picture text -->
BUR :<br>*NE-<br><!-- End of picture text -->

# Understanding CORS 

#### **What is CORS?** 

- Cross-Origin Resource Sharing 

- Security feature implemented by web browsers 



- Restricts web pages from making requests to a different domain 

Image from [Medianova] 

#### **Why is it Necessary?** 

   - Prevents malicious scripts on one page from obtaining access to sensitive data on another domain 

   - Helps protect against attacks like Cross-Site Scripting (XSS) and Cross-Site Request Forgery (CSRF) 

- **How CORS Works?** 

   - Browser sends a preflight request to check if cross-origin access is allowed 

   - The server responds with CORS headers defining what’s permitted 

#### **Common CORS Headers** 

- Access-Control-Allow-Origin: Specifies allowed origins 

- Access-Control-Allow-Methods: Lists allowed HTTP methods 

- Access-Control-Allow-Headers: Specifies allowed custom headers 



<!-- Start of picture text -->
SWIN<br>BUR 4m .<br>. NE-<br><!-- End of picture text -->

# Implementing CORS in FastAPI 

#### **Adding CORS Middleware** 

#### **Security Considerations** 

- Only allow necessary origins in production 

- Restrict methods and headers as needed 

#### **Testing CORS** 



<!-- Start of picture text -->
from fastapi.testclient import TestClient<br>from fastapi import FastAPI, HTTPException<br>app 19)<br># Adding CORS Middleware<br>from fastapi.middleware.cors import CORSMiddleware<br>app. (<br>CORSMiddleware,<br>allow_origins=["http://localhost:3000"],<br>allow_credentials 7<br>allow_methods=["x"]<br>allow_headers=["x"],<br>)<br># Testing CORS<br># Define the test client<br>client (app)<br># Test CORS support for the predict endpoint<br>def test ) r_predict():<br>response client. ("/api/predict")<br>assert "Access—Control-Allow-Origin" response. headers<br>assert response. headers ["Access—Control-Allow-Origin"]<br>http:// localhost: 3000<br># Test CORS support for the model-info endpoint<br>def test s_for el_info():<br>response = client. ("/api/model-info")<br>assert “Access-Control-Allow-Origin" response. headers<br>assert response. headers ["Access-Control-Allow-Origin"]<br>http:// localhost: 3000<br><!-- End of picture text -->



<!-- Start of picture text -->
SWiN<br>BUR<br><!-- End of picture text -->

# Visualizing AI Model Results in React 

#### **Choosing Visualization Libraries** 

- Recharts: Simple and customizable charts (e.g., line, bar, pie). 

- D3.js: Highly flexible, low-level control over visualizations. 

- Chart.js: Easy-to-use, supports various chart types, good for quick implementation. 

- Victory: A React-specific charting library focused on data visualization 

#### **Key Design Principles** 

- Keep the charts simple and intuitive, focus on clarity over complexity. 

- Use consistent color schemes to make data easy to distinguish. 

- Add tooltips and legends for better user interaction and understanding. 

#### **Responsive Design Tips** 

- Ensure visualizations are responsive to different screen sizes (desktop, tablet, mobile). 

- Use CSS media queries or built-in library features for responsive layouts. 

#### **Aesthetic Improvements** 

- Use smooth transitions. Consider animations to make charts feel more dynamic. 



<!-- Start of picture text -->
SWIN<br>BUR |e<br>*NE-<br><!-- End of picture text -->

# Visualizing AI Model Results (Assignment3) 

#### **Basic Requirements** 

- AI Model results are processed on the backend 

- Frontend receives ready-to-display images and data 

- Simple, effective display of results 

#### **Advanced Implementation (Optional)** 

- Implement interactive elements for higher scores 

- Examples of advanced features: 

1. Clickable data points for detailed 

view 



<!-- Start of picture text -->
e<br>Revenue: @1 2020 Expense: @1 2020 Profit: @1 2020 RrvenusrerEnriores Cee<br>$2.32M 1 $42.76K $516.76K 7 $110.01K 3.63K<br>Revenue vs Expense Trend Revenue by Projects Customers Distribution<br>©.<br>STABEK Stack $21437K<br>> ‘e<br>599 i)<br><!-- End of picture text -->

2. Zoom functionality for complex 

visualizations 

Image from [Zoho] 

3. Toggleable data layers or filters 



<!-- Start of picture text -->
SWIN<br>BUR .<br>*NE= ¢ae<br><!-- End of picture text -->

# Handling Long-Running Predictions 

#### **Implementing Websockets for Real-time Updates** 

- Set up a FastAPI WebSocket endpoint to send prediction progress updates. 

- Use a React WebSocket client to receive and display progress in real time. 

#### **Progress Indicators** 

- Display loading spinners or progress bars while waiting for predictions. 

- If possible, provide an estimated time remaining for the prediction to complete. 

#### **Async Predictions** 

- Use async processing in FastAPI to handle long-running predictions without blocking other requests. 

- Consider sending intermediate results or status updates to keep users informed. 

#### **User Experience Enhancements** 

- Notify the user when the prediction is done, either via a notification or by automatically updating the results on the UI. 

- Avoid freezing the UI during the prediction by keeping it responsive and interactive. 



<!-- Start of picture text -->
SWIN<br>BUR |e<br>*NE-<br><!-- End of picture text -->

# Error Handling in Practice 



<!-- Start of picture text -->
const [error, setError] ( 5<br>const makePredi async<br>try { () =>{<br>const response = await ("/api/predict", {<br>method: “POST",<br>headers: {<br>"Content-Type": “application/json",<br>x;<br>body: JSON. ({ input: inputData }),<br>});<br>if (!response.ok) {<br>+ throw new (response. statusText) ;<br>const data = await response. QO;<br>/ handle success<br>} catch (error) {<br>(error.message An error occurred");<br>}<br>3;<br>// In render<br>{error ErrorAlert message={error} />}<br><!-- End of picture text -->

**Client-Side Error Handling in React** 

- Handling API Errors: Ensure API call errors are caught and displayed in a user-friendly manner. 



<!-- Start of picture text -->
from fastapi import FastAPI, HTTPException<br>app ()<br>app. ("/api/predict")<br>async def predict(data: PredictionRequest):<br>try:<br>result = model. (data. input)<br>return {"prediction": result}<br>except asle.<br>raise (status_code=400, detail=f"\<br>Invalid input: {str(e)}")<br>_ Ache<br>except as e:<br>raise HT (status_code=500, detail="\<br>Internal server error")<br><!-- End of picture text -->

**Server-Side Error Handling in FastAPI** 

- Handling Predictive Errors: Ensure any errors during model prediction are caught and meaningful error messages are returned. 



<!-- Start of picture text -->
SWiN<br>BUR<br>*NE-<br><!-- End of picture text -->

# Error Handling and User Feedback 

#### **Improving User Feedback** 

- User-Friendly Error Messages: Avoid showing technical details to the user; instead, translate errors into understandable messages. 

Example: Instead of showing “500 Internal Server Error,” display “Something went wrong. 

Please try again later.” 

- Differentiate Between Error Types: Handle different error statuses (e.g., 400 for bad requests, 500 for server issues) and provide context to users. 

For a 400 error: “It looks like there was an issue with your input. Please check and try again.” **Best Practices for Error Handling** 

- Frontend: Always catch errors from API calls and ensure the user gets clear feedback. Consider adding retry mechanisms for transient errors. 

- Backend: Return descriptive and non-technical error messages while logging technical details for developers to diagnose. 

- General UX: Show a loading spinner while waiting for the prediction, and a clear error message if something goes wrong, so users aren’t left in uncertainty. 



Have a Break and Let’s continue with Lecture 02 



<!-- Start of picture text -->
ae |<br>is<br>= iy y<br><!-- End of picture text -->

Image from [Pinterest] 



<!-- Start of picture text -->
BUR amen<br>*NE*<br><!-- End of picture text -->

