# comp519_api_tester.py
import requests
import re
import json
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional, Callable

class COMP519APITester:
    def __init__(self, session_id: str, update_callback: Callable[[str, str], None] = None):
        self.session_id = session_id
        self.update_callback = update_callback or (lambda msg, type_: None)
        self.base_url = ""
        self.username = ""
        self.endpoints = []
        self.test_results = []
        
        self.test_player_data = {
            "givenNames": "John",
            "familyName": "Doe", 
            "nationality": "British",
            "dateOfBirth": "1995-05-15"
        }
        
        self.update_player_data = {
            "givenNames": "UpdatedJohn",
            "nationality": "American"
        }
        
        self.invalid_player_data = {
            "givenNames": "",
            "familyName": "Invalid",
            "nationality": "Unknown",
            "dateOfBirth": "invalid-date"
        }
        
        self.expected_endpoints = [
            {'method': 'GET', 'path': '/teams', 'type': 'get_teams'},
            {'method': 'GET', 'path': '/teams/{teamId}/players', 'type': 'get_players'},
            {'method': 'GET', 'path': '/teams/{teamId}/players/{playerId}', 'type': 'get_player'},
            {'method': 'POST', 'path': '/teams/{teamId}/players', 'type': 'add_player'},
            {'method': 'PATCH', 'path': '/teams/{teamId}/players/{playerId}', 'type': 'update_player'},
            {'method': 'DELETE', 'path': '/teams/{teamId}/players/{playerId}', 'type': 'delete_player'}
        ]
    
    def log(self, message: str, type_: str = 'info'):
        self.update_callback(message, type_)
    
    def test_api_from_html(self, html_content: str, username: str = None) -> Dict[str, Any]:
        try:
            self.log(f"Starting COMP519 REST API validation...")
            
            if username:
                self.username = username
            else:
                self.username = self.extract_username_from_html(html_content)
            
            if not self.username:
                raise Exception("Could not determine username for API testing")
            
            self.base_url = f"https://student.csc.liv.ac.uk/~{self.username}/v1"
            self.log(f"Testing API at: {self.base_url}")
            
            self.endpoints = self.parse_comp519_documentation(html_content)
            self.log(f"Found {len(self.endpoints)} documented endpoints")
            
            self.validate_required_endpoints()
            
            self.test_api_accessibility()
            
            self.run_comp519_tests()
            
            return self.compile_results()
            
        except Exception as e:
            self.log(f"Error during COMP519 API testing: {str(e)}", 'error')
            raise
    
    def extract_username_from_html(self, html_content: str) -> str:
        patterns = [
            r'student\.csc\.liv\.ac\.uk/~([a-zA-Z0-9]+)/',
            r'~([a-zA-Z0-9]+)/v1',
            r'Base URL:.*~([a-zA-Z0-9]+)/'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_content)
            if match:
                return match.group(1)
        
        return None
    
    def parse_comp519_documentation(self, html_content: str) -> List[Dict[str, Any]]:
        endpoints = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            description_section = soup.find('section', {'name': 'description'})
            if not description_section:
                description_section = soup.find('section', id='description')
            if not description_section:
                description_section = soup
            
            dt_elements = description_section.find_all('dt')
            
            for dt in dt_elements:
                dd = dt.find_next_sibling('dd')
                if not dd:
                    continue
                
                endpoint_info = self.extract_comp519_endpoint_info(dt, dd)
                if endpoint_info:
                    endpoints.append(endpoint_info)
                    self.log(f"Documented: {endpoint_info['method']} {endpoint_info['path']}")
            
            return endpoints
            
        except Exception as e:
            self.log(f"Error parsing COMP519 documentation: {str(e)}", 'error')
            return []
    
    def extract_comp519_endpoint_info(self, dt_element, dd_element) -> Optional[Dict[str, Any]]:
        try:
            dt_text = dt_element.get_text().strip()
            dd_text = dd_element.get_text().strip()
            dd_html = str(dd_element)
            
            if "request method" in dt_text.lower():
                method = dd_text.upper()
                path_dt = dt_element.find_next_sibling('dt')
                if path_dt and "resource path" in path_dt.get_text().lower():
                    path_dd = path_dt.find_next_sibling('dd')
                    if path_dd:
                        path = path_dd.get_text().strip()
                        endpoint_type = self.determine_comp519_endpoint_type(method, path)
                        
                        json_body = None
                        if method in ['POST', 'PATCH']:
                            sample_dt = path_dt.find_next_sibling('dt')
                            if sample_dt and "sample request body" in sample_dt.get_text().lower():
                                sample_dd = sample_dt.find_next_sibling('dd')
                                if sample_dd:
                                    json_body = self.extract_json_from_text(str(sample_dd))
                        
                        return {
                            'method': method,
                            'path': path,
                            'description': f"{dt_text}: {dd_text}",
                            'json_body': json_body,
                            'expected_status': self.get_expected_status(method, endpoint_type),
                            'type': endpoint_type
                        }
            
            return None
            
        except Exception as e:
            self.log(f"Error extracting COMP519 endpoint info: {str(e)}", 'error')
            return None
    
    def determine_comp519_endpoint_type(self, method: str, path: str) -> str:
        if path == '/teams' and method == 'GET':
            return 'get_teams'
        elif '/teams/' in path and '/players' in path:
            if path.endswith('/players') and method == 'GET':
                return 'get_players'
            elif path.endswith('/players') and method == 'POST':
                return 'add_player'
            elif path.count('/') == 4:
                if method == 'GET':
                    return 'get_player'
                elif method == 'PATCH':
                    return 'update_player'
                elif method == 'DELETE':
                    return 'delete_player'
        
        return 'unknown'
    
    def get_expected_status(self, method: str, endpoint_type: str) -> int:
        status_map = {
            'get_teams': 200,
            'get_players': 200,
            'get_player': 200,
            'add_player': 201,
            'update_player': 200,
            'delete_player': 204
        }
        return status_map.get(endpoint_type, 200)
    
    def validate_required_endpoints(self):
        documented_types = [ep['type'] for ep in self.endpoints]
        required_types = [ep['type'] for ep in self.expected_endpoints]
        
        missing_endpoints = []
        for req_ep in self.expected_endpoints:
            if req_ep['type'] not in documented_types:
                missing_endpoints.append(f"{req_ep['method']} {req_ep['path']}")
        
        if missing_endpoints:
            self.log(f"Missing required endpoints: {', '.join(missing_endpoints)}", 'warning')
        else:
            self.log("All required COMP519 endpoints are documented", 'success')
    
    def test_api_accessibility(self):
        try:
            self.log(f"Testing API accessibility at {self.base_url}")
            
            response = requests.get(f"{self.base_url}/teams", timeout=10)
            
            if response.status_code == 200:
                self.log("API is accessible and responding", 'success')
            elif response.status_code == 404:
                self.log("API endpoint not found - check if your web service is deployed", 'warning')
            elif response.status_code >= 500:
                self.log("API server error - check your implementation", 'error')
            else:
                self.log(f"API returned status {response.status_code}", 'info')
                
        except requests.ConnectionError:
            self.log("Cannot connect to API - ensure your web service is running", 'error')
        except requests.Timeout:
            self.log("API request timed out", 'error')
        except Exception as e:
            self.log(f"Error testing API accessibility: {str(e)}", 'error')
    
    def run_comp519_tests(self):
        test_scenarios = self.generate_comp519_test_scenarios()
        total_tests = len(test_scenarios)
        
        self.log(f"Starting {total_tests} COMP519 compliance tests")
        
        for i, scenario in enumerate(test_scenarios):
            progress = int(((i + 1) / total_tests) * 80) + 10  
            self.log(f"Running test {i+1}/{total_tests}: {scenario['name']}")
            
            result = self.execute_comp519_test(scenario)
            self.test_results.append(result)
            
            time.sleep(0.1)
    
    def generate_comp519_test_scenarios(self) -> List[Dict[str, Any]]:
        scenarios = []
        
        scenarios.append({
            'name': 'GET all teams - should return JSON array with 3 teams',
            'method': 'GET',
            'path': '/teams',
            'expected_status': 200,
            'body': None,
            'validation': 'teams_array'
        })
        
        scenarios.extend([
            {
                'name': 'GET players for team 1 - should return JSON array',
                'method': 'GET',
                'path': '/teams/1/players',
                'expected_status': 200,
                'body': None,
                'validation': 'players_array'
            },
            {
                'name': 'GET players for team 2 - should return JSON array',
                'method': 'GET',
                'path': '/teams/2/players',
                'expected_status': 200,
                'body': None,
                'validation': 'players_array'
            },
            {
                'name': 'GET players for team 3 - should return JSON array',
                'method': 'GET',
                'path': '/teams/3/players',
                'expected_status': 200,
                'body': None,
                'validation': 'players_array'
            }
        ])
        
        scenarios.append({
            'name': 'GET players for non-existent team - should return 404',
            'method': 'GET',
            'path': '/teams/999/players',
            'expected_status': 404,
            'body': None,
            'validation': None
        })
        
        scenarios.extend([
            {
                'name': 'GET specific player - should return player JSON',
                'method': 'GET',
                'path': '/teams/1/players/1',
                'expected_status': 200,
                'body': None,
                'validation': 'player_object'
            },
            {
                'name': 'GET non-existent player - should return 404',
                'method': 'GET',
                'path': '/teams/1/players/999',
                'expected_status': 404,
                'body': None,
                'validation': None
            }
        ])
        
        scenarios.extend([
            {
                'name': 'POST new player with valid data - should return 201',
                'method': 'POST',
                'path': '/teams/1/players',
                'expected_status': 201,
                'body': self.test_player_data,
                'validation': 'player_created'
            },
            {
                'name': 'POST player to non-existent team - should return 404',
                'method': 'POST',
                'path': '/teams/999/players',
                'expected_status': 404,
                'body': self.test_player_data,
                'validation': None
            },
            {
                'name': 'POST player with invalid data - should return 400',
                'method': 'POST',
                'path': '/teams/1/players',
                'expected_status': 400,
                'body': self.invalid_player_data,
                'validation': None
            }
        ])
        
        scenarios.extend([
            {
                'name': 'PATCH existing player - should return 200',
                'method': 'PATCH',
                'path': '/teams/1/players/1',
                'expected_status': 200,
                'body': self.update_player_data,
                'validation': 'player_updated'
            },
            {
                'name': 'PATCH non-existent player - should return 404',
                'method': 'PATCH',
                'path': '/teams/1/players/999',
                'expected_status': 404,
                'body': self.update_player_data,
                'validation': None
            }
        ])
        
        scenarios.extend([
            {
                'name': 'DELETE existing player - should return 204',
                'method': 'DELETE',
                'path': '/teams/1/players/2',
                'expected_status': 204,
                'body': None,
                'validation': None
            },
            {
                'name': 'DELETE non-existent player - should return 404',
                'method': 'DELETE',
                'path': '/teams/1/players/999',
                'expected_status': 404,
                'body': None,
                'validation': None
            }
        ])
        
        scenarios.extend([
            {
                'name': 'POST to /teams (not allowed) - should return 404',
                'method': 'POST',
                'path': '/teams',
                'expected_status': 404,
                'body': {"name": "New Team"},
                'validation': None
            },
            {
                'name': 'PUT to /teams/1 (not allowed) - should return 404',
                'method': 'PUT',
                'path': '/teams/1',
                'expected_status': 404,
                'body': {"name": "Updated Team"},
                'validation': None
            }
        ])
        
        return scenarios
    
    def execute_comp519_test(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        try:
            url = self.base_url + scenario['path']
            headers = {'Content-Type': 'application/json'} if scenario['body'] else {}
            
            response = self.send_request(scenario['method'], url, headers, scenario['body'])
            
            result = self.analyze_comp519_response(scenario, response)
            
            return result
            
        except Exception as e:
            return {
                'test_name': scenario['name'],
                'method': scenario['method'],
                'path': scenario['path'],
                'status': 'error',
                'message': str(e),
                'expected_status': scenario['expected_status'],
                'actual_status': None,
                'response_body': None,
                'url': f"{self.base_url}{scenario['path']}"
            }
    
    def send_request(self, method: str, url: str, headers: Dict, json_body: Any) -> requests.Response:
        try:
            kwargs = {'headers': headers, 'timeout': 10}
            if json_body:
                kwargs['json'] = json_body
            
            if method == 'GET':
                response = requests.get(url, **kwargs)
            elif method == 'POST':
                response = requests.post(url, **kwargs)
            elif method == 'PATCH':
                response = requests.patch(url, **kwargs)
            elif method == 'PUT':
                response = requests.put(url, **kwargs)
            elif method == 'DELETE':
                response = requests.delete(url, **kwargs)
            else:
                raise Exception(f"Unsupported HTTP method: {method}")
            
            return response
            
        except requests.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def analyze_comp519_response(self, scenario: Dict, response: requests.Response) -> Dict[str, Any]:
        result = {
            'test_name': scenario['name'],
            'method': scenario['method'],
            'path': scenario['path'],
            'expected_status': scenario['expected_status'],
            'actual_status': response.status_code,
            'url': response.url
        }
        
        status_match = response.status_code == scenario['expected_status']
        
        response_body = None
        content_type_ok = True
        
        if response.text:
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    response_body = response.json()
                except json.JSONDecodeError:
                    content_type_ok = False
                    response_body = response.text
            else:
                response_body = response.text
        
        result['response_body'] = response_body
        
        validation_passed = True
        validation_message = ""
        
        if scenario.get('validation') and status_match:
            validation_passed, validation_message = self.validate_comp519_response(
                scenario['validation'], response_body
            )
        
        if status_match and content_type_ok and validation_passed:
            result['status'] = 'pass'
            result['message'] = 'Test passed - meets COMP519 requirements'
        elif status_match and content_type_ok:
            result['status'] = 'warning'
            result['message'] = f'Status correct but validation issue: {validation_message}'
        elif status_match:
            result['status'] = 'warning'
            result['message'] = 'Status correct but response format issues'
        else:
            result['status'] = 'fail'
            result['message'] = f'Expected status {scenario["expected_status"]}, got {response.status_code}'
        
        return result
    
    def validate_comp519_response(self, validation_type: str, response_body: Any) -> tuple[bool, str]:
        try:
            if validation_type == 'teams_array':
                if not isinstance(response_body, list):
                    return False, "Response should be a JSON array"
                if len(response_body) != 3:
                    return False, f"Expected 3 teams, got {len(response_body)}"
                for team in response_body:
                    if not isinstance(team, dict):
                        return False, "Each team should be a JSON object"
                    required_fields = ['name', 'sport']
                    for field in required_fields:
                        if field not in team:
                            return False, f"Team missing required field: {field}"
                return True, "Valid teams array"
                
            elif validation_type == 'players_array':
                if not isinstance(response_body, list):
                    return False, "Response should be a JSON array"
                for player in response_body:
                    if not isinstance(player, dict):
                        return False, "Each player should be a JSON object"
                    required_fields = ['givenNames', 'familyName', 'nationality', 'dateOfBirth']
                    for field in required_fields:
                        if field not in player:
                            return False, f"Player missing required field: {field}"
                return True, "Valid players array"
                
            elif validation_type == 'player_object':
                if not isinstance(response_body, dict):
                    return False, "Response should be a JSON object"
                required_fields = ['givenNames', 'familyName', 'nationality', 'dateOfBirth']
                for field in required_fields:
                    if field not in response_body:
                        return False, f"Player missing required field: {field}"
                return True, "Valid player object"
                
            elif validation_type == 'player_created':
                if not isinstance(response_body, dict):
                    return False, "Response should be a JSON object"
                if 'id' not in response_body and 'givenNames' not in response_body:
                    return False, "Response should contain player data or ID"
                return True, "Player creation response valid"
                
            elif validation_type == 'player_updated':
                if not isinstance(response_body, dict):
                    return False, "Response should be a JSON object"
                return True, "Player update response valid"
                
            return True, "No validation specified"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def extract_json_from_text(self, text: str) -> Optional[Dict]:
        try:
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, text, re.DOTALL)
            
            for match in matches:
                try:
                    cleaned = re.sub(r'<[^>]+>', '', match)
                    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                    return json.loads(cleaned)
                except json.JSONDecodeError:
                    continue
            
            return None
            
        except Exception:
            return None
    
    def compile_results(self) -> Dict[str, Any]:
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'pass'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'fail'])
        warning_tests = len([r for r in self.test_results if r['status'] == 'warning'])
        error_tests = len([r for r in self.test_results if r['status'] == 'error'])
        
        compliance_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        comp519_summary = self.generate_comp519_summary()
        
        return {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'warnings': warning_tests,
                'errors': error_tests,
                'success_rate': compliance_score,
                'comp519_compliance': compliance_score
            },
            'comp519_summary': comp519_summary,
            'endpoints': self.endpoints,
            'test_results': self.test_results,
            'base_url': self.base_url,
            'username': self.username
        }
    
    def generate_comp519_summary(self) -> Dict[str, Any]:
        endpoint_results = {}
        
        for result in self.test_results:
            path = result['path']
            method = result['method']
            endpoint_key = f"{method} {path}"
            
            if endpoint_key not in endpoint_results:
                endpoint_results[endpoint_key] = []
            endpoint_results[endpoint_key].append(result)
        
        required_compliance = {}
        for req_ep in self.expected_endpoints:
            endpoint_key = f"{req_ep['method']} {req_ep['path']}"
            tests = [r for r in self.test_results if r['method'] == req_ep['method'] and 
                    self.normalize_path(r['path']) == self.normalize_path(req_ep['path'])]
            
            if tests:
                passed = len([t for t in tests if t['status'] == 'pass'])
                total = len(tests)
                required_compliance[endpoint_key] = {
                    'implemented': True,
                    'passed_tests': passed,
                    'total_tests': total,
                    'success_rate': (passed / total * 100) if total > 0 else 0
                }
            else:
                required_compliance[endpoint_key] = {
                    'implemented': False,
                    'passed_tests': 0,
                    'total_tests': 0,
                    'success_rate': 0
                }
        
        return {
            'endpoint_compliance': required_compliance,
            'all_endpoints_implemented': all(comp['implemented'] for comp in required_compliance.values()),
            'json_compliance': self.check_json_compliance(),
            'http_status_compliance': self.check_status_compliance(),
            'documentation_compliance': len(self.endpoints) >= 6
        }
    
    def normalize_path(self, path: str) -> str:
        normalized = re.sub(r'/\d+/', '/{id}/', path)
        normalized = re.sub(r'/\d+,' ,'/{id}', normalized)
        return normalized
    
    def check_json_compliance(self) -> bool:
        json_tests = [r for r in self.test_results if r['status'] == 'pass' and 
                     r['response_body'] and isinstance(r['response_body'], (dict, list))]
        total_success_tests = [r for r in self.test_results if r['status'] == 'pass']
        
        if not total_success_tests:
            return False
        
        return len(json_tests) / len(total_success_tests) >= 0.8  
    
    def check_status_compliance(self) -> bool:
        correct_status_tests = [r for r in self.test_results if 
                               r['actual_status'] == r['expected_status']]
        
        if not self.test_results:
            return False
        
        return len(correct_status_tests) / len(self.test_results) >= 0.8 