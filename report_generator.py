import os
import json
from datetime import datetime
from typing import Dict, Any

class ReportGenerator:
    def __init__(self):
        self.reports_folder = 'reports'
        os.makedirs(self.reports_folder, exist_ok=True)
    
    def generate_comp519_report(self, results: Dict[str, Any], username: str, session_id: str) -> str:
        
        summary = results.get('summary', {})
        comp519_summary = results.get('comp519_summary', {})
        test_results = results.get('test_results', [])
        base_url = results.get('base_url', '')
        
        compliance_score = summary.get('comp519_compliance', 0)
        grade_info = self.calculate_comp519_grade(compliance_score, comp519_summary)
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>COMP519 Assignment 4 - API Test Report - {username}</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f8fafc;
            padding: 20px;
            margin-right: 320px; /* Space for navigation */
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 25px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }}
        
        .header .subtitle {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        
        .student-info {{
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 1rem;
            margin: 1rem;
            border-radius: 8px;
        }}
        
        .content {{
            padding: 2rem;
        }}
        
        .section {{
            margin-bottom: 2rem;
            padding: 1.5rem;
            border-radius: 8px;
            border: 1px solid #e5e5e5;
        }}
        
        .section h2 {{
            color: #2c3e50;
            margin-bottom: 1rem;
            font-size: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .grade-section {{
            background: linear-gradient(135deg, {grade_info['bg_color']});
            border: 2px solid {grade_info['border_color']};
            text-align: center;
        }}
        
        .grade-score {{
            font-size: 3rem;
            font-weight: bold;
            color: {grade_info['text_color']};
            margin: 1rem 0;
        }}
        
        .grade-description {{
            font-size: 1.1rem;
            color: #555;
            margin-bottom: 1rem;
        }}
        
        .compliance-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }}
        
        .compliance-card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 1rem;
            border-left: 4px solid #28a745;
        }}
        
        .compliance-card.warning {{
            border-left-color: #ffc107;
        }}
        
        .compliance-card.error {{
            border-left-color: #dc3545;
        }}
        
        .endpoints-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
        }}
        
        .endpoints-table th,
        .endpoints-table td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        
        .endpoints-table th {{
            background-color: #f8f9fa;
            font-weight: 600;
        }}
        
        .method-badge {{
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .method-get {{ background: #dbeafe; color: #1e40af; }}
        .method-post {{ background: #dcfce7; color: #166534; }}
        .method-patch {{ background: #fef3c7; color: #92400e; }}
        .method-delete {{ background: #fee2e2; color: #991b1b; }}
        
        .status-badge {{
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .status-pass {{ background: #dcfce7; color: #166534; }}
        .status-fail {{ background: #fee2e2; color: #991b1b; }}
        .status-warning {{ background: #fef3c7; color: #92400e; }}
        .status-error {{ background: #f3f4f6; color: #374151; }}
        
        .test-details {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
            border-left: 4px solid #6c757d;
        }}
        
        .test-details.pass {{
            border-left-color: #28a745;
            background: #f8fff9;
        }}
        
        .test-details.fail {{
            border-left-color: #dc3545;
            background: #fff8f8;
        }}
        
        .test-details.warning {{
            border-left-color: #ffc107;
            background: #fffbf0;
        }}
        
        .json-viewer {{
            background: #2d3748;
            color: #e2e8f0;
            padding: 1rem;
            border-radius: 8px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.875rem;
            overflow-x: auto;
            margin: 0.5rem 0;
        }}
        
        .recommendations {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }}
        
        .recommendations h3 {{
            color: #856404;
            margin-bottom: 0.5rem;
        }}
        
        .recommendations ul {{
            color: #856404;
            margin-left: 1rem;
        }}
        
        .footer {{
            text-align: center;
            padding: 2rem;
            background: #f8f9fa;
            color: #6c757d;
            font-size: 0.875rem;
        }}
        
        @media (max-width: 768px) {{
            body {{
                margin-right: 0;
                padding: 10px;
            }}
            
            .compliance-grid {{
                grid-template-columns: 1fr;
            }}
            
            .endpoints-table {{
                font-size: 0.875rem;
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
        }}
        
        @media print {{
            body {{
                margin-right: 0;
                background: white;
            }}
            
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-graduation-cap"></i> API Tester</h1>
            <div class="subtitle">REST API Implementation Test Report</div>
        </div>
        
        <div class="student-info">
            <strong>Student:</strong> {username} &nbsp;&nbsp;&nbsp;
            <strong>API Base URL:</strong> {base_url} &nbsp;&nbsp;&nbsp;
            <strong>Test Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} &nbsp;&nbsp;&nbsp;
            <strong>Session ID:</strong> {session_id[:8]}...
        </div>
        
        <div class="content">
            <!-- Grade Summary Section -->
            <div class="section grade-section" id="grade-summary">
                <h2><i class="fas fa-award"></i> Overall Assessment</h2>
                <div class="grade-score">{compliance_score:.1f}%</div>
                <div class="grade-description">{grade_info['description']}</div>
                <div style="font-size: 0.9rem; color: #666;">
                    Based on {summary.get('total_tests', 0)} comprehensive test scenarios
                </div>
            </div>
            
            <!-- COMP519 Compliance Check -->
            <div class="section" id="compliance-check">
                <h2><i class="fas fa-check-circle"></i> test Requirements Compliance</h2>
                <div class="compliance-grid">
                    {self.generate_compliance_cards(comp519_summary)}
                </div>
            </div>
            
            <!-- API Endpoints Summary -->
            <div class="section" id="endpoints-summary">
                <h2><i class="fas fa-network-wired"></i> API Endpoints Testing</h2>
                <table class="endpoints-table">
                    <thead>
                        <tr>
                            <th>Method</th>
                            <th>Endpoint</th>
                            <th>Tests Run</th>
                            <th>Status</th>
                            <th>Success Rate</th>
                        </tr>
                    </thead>
                    <tbody>
                        {self.generate_endpoints_table(comp519_summary.get('endpoint_compliance', {}))}
                    </tbody>
                </table>
            </div>
            
            <!-- Detailed Test Results -->
            <div class="section" id="test-results">
                <h2><i class="fas fa-list-alt"></i> Detailed Test Results</h2>
                {self.generate_detailed_results(test_results)}
            </div>
            
            {self.generate_recommendations(compliance_score, comp519_summary)}
        </div>
        
        <div class="footer" id="footer">
            <p>Generated by TestFlow Pro - COMP519 API Validator</p>
            <p>University of Liverpool - Department of Computer Science</p>
            <p>This report validates compliance with COMP519 Assignment 4 requirements</p>
        </div>
    </div>
</body>
</html>"""
        
        return html_content
    
    def calculate_comp519_grade(self, compliance_score: float, comp519_summary: Dict) -> Dict[str, str]:

        
        if compliance_score >= 90:
            return {
                'description': 'Excellent - Exceeds test requirements',
                'bg_color': '#d4edda, #c3e6cb',
                'border_color': '#28a745',
                'text_color': '#155724'
            }
        elif compliance_score >= 80:
            return {
                'description': 'Very Good - Meets most test requirements',
                'bg_color': '#e2f3ff, #b8e6ff',
                'border_color': '#007bff',
                'text_color': '#004085'
            }
        elif compliance_score >= 70:
            return {
                'description': 'Good - Meets basic test requirements',
                'bg_color': '#fff3cd, #ffeaa7',
                'border_color': '#ffc107',
                'text_color': '#856404'
            }
        elif compliance_score >= 60:
            return {
                'description': 'Satisfactory - Some test requirements missing',
                'bg_color': '#ffeaa7, #fdcb6e',
                'border_color': '#fd7e14',
                'text_color': '#8b4513'
            }
        else:
            return {
                'description': 'Needs Improvement - Major test requirements missing',
                'bg_color': '#f8d7da, #f5c6cb',
                'border_color': '#dc3545',
                'text_color': '#721c24'
            }
    
    def generate_compliance_cards(self, comp519_summary: Dict) -> str:
        cards = []
        
        all_endpoints = comp519_summary.get('all_endpoints_implemented', False)
        card_class = 'compliance-card' if all_endpoints else 'compliance-card error'
        icon = 'fas fa-check-circle' if all_endpoints else 'fas fa-times-circle'
        status = 'All Required Endpoints' if all_endpoints else 'Missing Endpoints'
        
        cards.append(f"""
        <div class="{card_class}">
            <h4><i class="{icon}"></i> {status}</h4>
            <p>{'✓ All 6 required endpoints documented and tested' if all_endpoints else '✗ Some required endpoints are missing'}</p>
        </div>
        """)
        
        json_compliance = comp519_summary.get('json_compliance', False)
        card_class = 'compliance-card' if json_compliance else 'compliance-card warning'
        icon = 'fas fa-code' if json_compliance else 'fas fa-exclamation-triangle'
        status = 'JSON Format' if json_compliance else 'JSON Issues'
        
        cards.append(f"""
        <div class="{card_class}">
            <h4><i class="{icon}"></i> {status}</h4>
            <p>{'✓ Proper JSON request/response format' if json_compliance else '⚠ Some JSON format issues detected'}</p>
        </div>
        """)
        
        status_compliance = comp519_summary.get('http_status_compliance', False)
        card_class = 'compliance-card' if status_compliance else 'compliance-card warning'
        icon = 'fas fa-exchange-alt' if status_compliance else 'fas fa-exclamation-triangle'
        status = 'HTTP Status Codes' if status_compliance else 'Status Code Issues'
        
        cards.append(f"""
        <div class="{card_class}">
            <h4><i class="{icon}"></i> {status}</h4>
            <p>{'✓ Correct HTTP status codes used' if status_compliance else '⚠ Some incorrect status codes detected'}</p>
        </div>
        """)
        
        doc_compliance = comp519_summary.get('documentation_compliance', False)
        card_class = 'compliance-card' if doc_compliance else 'compliance-card error'
        icon = 'fas fa-file-alt' if doc_compliance else 'fas fa-times-circle'
        status = 'Documentation' if doc_compliance else 'Documentation Issues'
        
        cards.append(f"""
        <div class="{card_class}">
            <h4><i class="{icon}"></i> {status}</h4>
            <p>{'✓ Complete API documentation provided' if doc_compliance else '✗ Incomplete or missing documentation'}</p>
        </div>
        """)
        
        return ''.join(cards)
    
    def generate_endpoints_table(self, endpoint_compliance: Dict) -> str:
        rows = []
        
        expected_endpoints = [
            ('GET', '/teams'),
            ('GET', '/teams/{teamId}/players'),
            ('GET', '/teams/{teamId}/players/{playerId}'),
            ('POST', '/teams/{teamId}/players'),
            ('PATCH', '/teams/{teamId}/players/{playerId}'),
            ('DELETE', '/teams/{teamId}/players/{playerId}')
        ]
        
        for method, path in expected_endpoints:
            endpoint_key = f"{method} {path}"
            compliance = endpoint_compliance.get(endpoint_key, {})
            
            implemented = compliance.get('implemented', False)
            passed_tests = compliance.get('passed_tests', 0)
            total_tests = compliance.get('total_tests', 0)
            success_rate = compliance.get('success_rate', 0)
            
            status_class = 'status-pass' if implemented and success_rate > 80 else 'status-fail' if not implemented else 'status-warning'
            status_text = 'Implemented' if implemented else 'Missing'
            if implemented and success_rate <= 80:
                status_text = 'Issues'
            
            rows.append(f"""
            <tr>
                <td><span class="method-badge method-{method.lower()}">{method}</span></td>
                <td><code>{path}</code></td>
                <td>{passed_tests}/{total_tests}</td>
                <td><span class="status-badge {status_class}">{status_text}</span></td>
                <td>{success_rate:.1f}%</td>
            </tr>
            """)
        
        return ''.join(rows)
    
    def generate_detailed_results(self, test_results: list) -> str:
        if not test_results:
            return '<p>No test results available.</p>'
        
        results_html = []
        
        grouped_results = {}
        for result in test_results:
            endpoint = f"{result.get('method', 'UNKNOWN')} {result.get('path', 'unknown')}"
            if endpoint not in grouped_results:
                grouped_results[endpoint] = []
            grouped_results[endpoint].append(result)
        
        for endpoint, results in grouped_results.items():
            results_html.append(f'<h3>{endpoint}</h3>')
            
            for result in results:
                status_class = result.get('status', 'error')
                test_name = result.get('test_name', 'Unknown test')
                message = result.get('message', 'No message')
                expected_status = result.get('expected_status', 'N/A')
                actual_status = result.get('actual_status', 'N/A')
                response_body = result.get('response_body')
                
                response_html = ''
                if response_body:
                    if isinstance(response_body, (dict, list)):
                        response_html = f'<div class="json-viewer">{json.dumps(response_body, indent=2)}</div>'
                    else:
                        response_html = f'<div class="json-viewer">{str(response_body)}</div>'
                
                results_html.append(f"""
                <div class="test-details {status_class}">
                    <h4><i class="fas fa-{'check' if status_class == 'pass' else 'times' if status_class == 'fail' else 'exclamation-triangle'}"></i> {test_name}</h4>
                    <p><strong>Status:</strong> <span class="status-badge status-{status_class}">{status_class.upper()}</span></p>
                    <p><strong>Message:</strong> {message}</p>
                    <p><strong>Expected Status:</strong> {expected_status} &nbsp;&nbsp; <strong>Actual Status:</strong> {actual_status}</p>
                    {response_html}
                </div>
                """)
        
        return ''.join(results_html)
    
    def generate_recommendations(self, compliance_score: float, comp519_summary: Dict) -> str:
        recommendations = []
        
        if not comp519_summary.get('all_endpoints_implemented', False):
            recommendations.append("Implement all required REST endpoints as specified in the assignment")
        
        if not comp519_summary.get('json_compliance', False):
            recommendations.append("Ensure all responses use proper JSON format with correct Content-Type headers")
        
        if not comp519_summary.get('http_status_compliance', False):
            recommendations.append("Use appropriate HTTP status codes (200, 201, 204, 404, 400) as specified")
        
        if compliance_score < 70:
            recommendations.append("Review the assignment requirements and ensure your API matches the specified interface")
            recommendations.append("Test your API manually using the provided interface.html file")
        
        if compliance_score < 90:
            recommendations.append("Add proper error handling for edge cases (non-existent resources, invalid data)")
            recommendations.append("Ensure your database contains exactly 3 teams with 3 players each initially")
        
        if not recommendations:
            recommendations.append("Excellent work! Your API implementation meets all requirements")
            recommendations.append("Consider adding additional validation and error handling for extra robustness")
        
        if recommendations:
            rec_html = '<div class="recommendations">'
            rec_html += '<h3><i class="fas fa-lightbulb"></i> Recommendations</h3>'
            rec_html += '<ul>'
            for rec in recommendations:
                rec_html += f'<li>{rec}</li>'
            rec_html += '</ul></div>'
            return rec_html
        
        return ''
    
    def generate_comp519_html_report(self, results: Dict[str, Any], username: str, session_id: str) -> str:
        report_content = self.generate_comp519_report(results, username, session_id)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'comp519_{username}_{session_id[:8]}_{timestamp}.html'
        filepath = os.path.join(self.reports_folder, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return filepath