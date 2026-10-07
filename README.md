# EndpointValidator
# Automated REST API Testing Framework

An automated testing framework developed as my **MSc Computer Science dissertation project at the University of Liverpool**.

The project automatically tests and evaluates student-developed RESTful APIs by parsing their HTML API documentation, generating test scenarios, sending HTTP/HTTPS requests, validating responses, and producing structured test reports.

## Features

* Parses API documentation using **BeautifulSoup**
* Uses **Regular Expressions** to extract endpoints, HTTP methods, URL parameters, and JSON data
* Automatically generates valid and invalid API test scenarios
* Tests REST API endpoints using HTTP/HTTPS requests
* Validates HTTP status codes and JSON response structure
* Handles asynchronous test execution using Flask
* Generates downloadable **CSV test reports**
* Provides a simple web interface for starting tests and viewing results

## Tech Stack

* **Python**
* **Flask**
* **BeautifulSoup4**
* **Requests**
* **Regular Expressions**
* **HTML5 / CSS3**
* **JavaScript**
* **CSV**

The system uses a three-tier architecture consisting of a web interface, Flask backend, and automated testing engine.

## How It Works

```text
Student API Documentation
          ↓
   Documentation Parser
          ↓
   Test Scenario Generator
          ↓
      HTTP Requests
          ↓
 Response Validation
          ↓
     Test Results
          ↓
      CSV Report
```

The framework was evaluated against multiple student REST APIs and successfully identified issues such as incorrect HTTP status codes, missing functionality, malformed JSON responses, and server failures.

## Project Outcome

The project demonstrated that automated testing can reduce the manual effort involved in assessing RESTful APIs while providing consistent and structured feedback.

A key limitation identified was that fixed test data could struggle with variations in API field naming and schemas. Future improvements could include more adaptive and schema-aware test generation.

## Academic Project

**MSc Computer Science — COMP702**
**University of Liverpool**
**2024/25**
