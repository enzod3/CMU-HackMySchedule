<!-- PROJECT LOGO -->
<br />
<p align="center">
  <img src="./screenshots/courses.png">
  <h3 align="center">CMU HackMySchedule</h3>
  <p align="center">
    A schedule planning application for Carnegie Mellon students.
    <br />
    <a href="https://www.youtube.com/watch?v=pWDo0WaSeV4"><strong>Demo Video»</strong></a>
    <br />
  </p>
</p>

<!-- TABLE OF CONTENTS -->
<h2 id="table-of-contents">Table of Contents</h2>
<ul>
<li><a href="#about-the-project">About the Project</a><ul>
<li><a href="#built-with">Built With</a></li>
</ul>
</li>
<li><a href="#getting-started">Getting Started</a><ul>
<li><a href="#prerequisites">Prerequisites</a></li>
<li><a href="#installation">Installation</a></li>
</ul>
</li>
<li><a href="#usage">Usage</a></li>
<li><a href="#contributing">Contributing</a></li>
<li><a href="#license">License</a></li>
</ul>
<!-- ABOUT THE PROJECT -->
<h2 id="about-the-project">About The Project</h2>
This application was the final submission to CMU's 15-112 term project assignment. Other projects like this can be seen on the course's <a href="https://www.cs.cmu.edu/~112/index.html">homepage</a>. This project and 11 others were recognized at the end of the Course as unique out of 300 total projects.
<br />
<br />
<p>HackMySchedule is a schedule planner designed to assist students at Carnegie Mellon plan their schedules. It offers a user-friendly interface to rank various course combinations, helping you find the schedule that best fits your needs and preferences. It uses CMU&#39;s course catalog and student/teacher evaluations to rank schedules (using some dynamic programming approaches) based on Workload, Instructor Rating, and Median Break. Specific lectures and recitations can be blacklisted to give more control over a schedule. </p>
<p>Current Features</p>
<ul>
<li>Schedule View</li>
<li>Course adding, removing and editing</li>
<li>Recitation and lecture blacklisting</li>
<li>Schedule sorting</li>
</ul>
<h3 id="built-with">Built With</h3>
<ul>
<li><a href="https://www.python.org/">Python</a></li>
<li>Cmu_graphics, Pandas</li>
</ul>
<!-- GETTING STARTED -->
<h2 id="getting-started">Getting Started</h2>
<p>To run HackMySchedule, follow these steps.</p>
<h3 id="prerequisites">Prerequisites</h3>
<ul>
<li>Python</li>
</ul>
<h3 id="installation">Installation</h3>
<ol>
<li>Clone the repo</li>
</ol>
<pre class="codeblock language-sh">git <span class="hljs-built_in">clone</span> https://github.com/enzod3/CMU-HackMySchedule
</pre>
<ol start="2">
<li>Install the required packages</li>
</ol>
<pre class="codeblock language-sh">pip install cmu_graphics pandas
</pre>
<ol start="3">
<li>Start the program</li>
</ol>
<pre class="codeblock language-sh"><span class="hljs-built_in">cd</span> src
python main.py
</pre>
<!-- Usage-->
<h2 id="usage">Usage</h2>

<h3>Schedules View</h3>
<img src="./screenshots/schedules.png">

<table>
  <tr>
    <td><strong>Pagination</strong></td>
    <td><kbd>←</kbd>, <kbd>→</kbd></td>
  </tr>
  <tr>
    <td><strong>CourseID Input</strong></td>
    <td>Type numbers</td>
  </tr>
  <tr>
    <td><strong>GroupName Input</strong></td>
    <td>Type letters</td>
  </tr>
  <tr>
    <td><strong>Add Course</strong></td>
    <td><kbd>⏎ Enter</kbd></td>
  </tr>
  <tr>
    <td><strong>View Course</strong></td>
    <td>Click Course</td>
  </tr>
</table>
<br />

<h3>Courses View</h3>
<img src="./screenshots/courses.png">

<table>
  <tr>
    <td><strong>Pagination</strong></td>
    <td><kbd>←</kbd>, <kbd>→</kbd></td>
  </tr>
</table>
<br />

<h3>Sections View</h3>
<img src="./screenshots/sections.png">

<table>
  <tr>
    <td><strong>Pagination</strong></td>
    <td><kbd>←</kbd>, <kbd>→</kbd></td>
  </tr>
  <tr>
    <td><strong>Blacklist</strong></td>
    <td>Click Section</td>
  </tr>
</table>
<br />

<!-- CONTRIBUTING -->
<h2 id="contributing">Contributing</h2>
<p>Interested in contributing to HackMySchedule? Here&#39;s how you can help:</p>
<ul>
<li><strong>Reporting Bugs</strong></li>
<li><strong>Suggesting Enhancements</strong></li>
<li><strong>Sending Pull Requests</strong></li>
</ul>
<!-- LICENSE -->
<h2 id="license">License</h2>
<p>Distributed under the MIT License.</p>
