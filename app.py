# app.py - Modified for COMP519 API Testing
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import os
import json
from datetime import datetime
import uuid
import logging
from comp519_api_tester import COMP519APITester
from report_generator import ReportGenerator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'testflow-pro-comp519-secret-key-2024'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['REPORTS_FOLDER'] = 'reports'

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Store test sessions in memory (in production, use Redis or database)
test_sessions = {}

@app.route('/')
def index():
    """Main landing page for COMP519 API testing"""
    return render_template('index.html')

@app.route('/api/start-test', methods=['POST'])
def start_test():
    """Start COMP519 API testing process"""
    try:
        data = request.json
        html_content = data.get('htmlContent', '').strip()
        file_name = data.get('fileName', 'comp519_api.html')
        username = data.get('username', '').strip()
        
        if not html_content:
            return jsonify({'error': 'HTML content is required'}), 400
        
        if not username:
            return jsonify({'error': 'Username is required for COMP519 testing'}), 400
        
        # Validate username format
        if not username.isalnum():
            return jsonify({'error': 'Username should contain only letters and numbers'}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Initialize test session
        test_sessions[session_id] = {
            'status': 'starting',
            'progress': 0,
            'logs': [],
            'results': None,
            'html_content': html_content,
            'file_name': file_name,
            'username': username,
            'start_time': datetime.now().isoformat(),
            'end_time': None
        }
        
        # Start testing in background
        import threading
        thread = threading.Thread(target=run_comp519_tests, args=(session_id, html_content, username))
        thread.daemon = True
        thread.start()
        
        return jsonify({'sessionId': session_id, 'status': 'started'})
    
    except Exception as e:
        logging.error(f"Failed to start COMP519 test: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-status/<session_id>')
def test_status(session_id):
    """Get COMP519 test progress and logs"""
    session = test_sessions.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    return jsonify({
        'status': session['status'],
        'progress': session['progress'],
        'logs': session['logs'][-50:],  # Return last 50 logs
        'completed': session['status'] in ['completed', 'failed'],
        'username': session.get('username', '')
    })

@app.route('/report/<session_id>')
def view_report(session_id):
    """View COMP519 test report in browser"""
    session = test_sessions.get(session_id)
    if not session:
        return render_template('error.html', 
                             error_title="Session Not Found",
                             error_message="The requested test session could not be found. It may have expired or been removed."), 404
    
    if session['status'] != 'completed':
        return render_template('error.html', 
                             error_title="Report Not Available",
                             error_message="The COMP519 test report is not available yet. Please wait for testing to complete or try again later."), 404
    
    try:
        # Generate the COMP519 report content
        report_generator = ReportGenerator()
        results = session['results']
        file_name = session.get('file_name', 'comp519_api.html')
        username = session.get('username', 'unknown')
        
        # Get the report HTML content with COMP519 customizations
        report_html = report_generator.generate_comp519_report(results, username, session_id)
        
        # Inject enhanced navigation into the report
        enhanced_report = inject_comp519_navigation(report_html, session_id, session)
        
        return enhanced_report
    
    except Exception as e:
        logging.error(f"Failed to view COMP519 report for session {session_id}: {str(e)}", exc_info=True)
        return render_template('error.html',
                             error_title="Report Generation Failed",
                             error_message=f"Failed to generate COMP519 report: {str(e)}"), 500

def inject_comp519_navigation(report_html, session_id, session):
    """Inject COMP519-specific navigation into the report HTML"""
    
    # Calculate session duration
    start_time = datetime.fromisoformat(session['start_time'])
    end_time = datetime.fromisoformat(session.get('end_time', session['start_time']))
    duration = (end_time - start_time).total_seconds()
    
    # Get summary stats for navigation
    results = session.get('results', {})
    summary = results.get('summary', {})
    username = session.get('username', 'unknown')
    
    navigation_html = f"""
    <!-- COMP519 Enhanced Navigation Panel -->
    <div id="report-navigation" style="
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        display: flex;
        flex-direction: column;
        gap: 15px;
        background: rgba(255, 255, 255, 0.98);
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
        backdrop-filter: blur(30px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        min-width: 300px;
        transition: all 0.3s ease;
    ">
        <!-- Navigation Header -->
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(107, 114, 128, 0.2);
        ">
            <div style="
                font-weight: 700;
                font-size: 1.1rem;
                color: #111827;
                display: flex;
                align-items: center;
                gap: 8px;
            ">
                <i class="fas fa-graduation-cap" style="color: #10b981;"></i>
                COMP519 Report
            </div>
            <button onclick="toggleNavigation()" style="
                background: none;
                border: none;
                color: #6b7280;
                cursor: pointer;
                padding: 5px;
                border-radius: 5px;
                transition: all 0.2s ease;
            " onmouseover="this.style.color='#111827'" onmouseout="this.style.color='#6b7280'">
                <i class="fas fa-eye-slash"></i>
            </button>
        </div>
        
        <!-- Student Info -->
        <div style="
            background: linear-gradient(135deg, #e0f2fe, #b3e5fc);
            border: 1px solid #0288d1;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 10px;
        ">
            <div style="
                font-size: 0.9rem;
                color: #01579b;
                margin-bottom: 5px;
            ">
                <strong>Student:</strong> {username}
            </div>
            <div style="
                font-size: 0.85rem;
                color: #0277bd;
            ">
                <strong>API URL:</strong> 
                <span style="font-family: monospace; font-size: 0.8rem;">
                    student.csc.liv.ac.uk/~{username}/v1
                </span>
            </div>
        </div>
        
        <!-- Quick Stats -->
        <div style="
            background: linear-gradient(135deg, #f0fdf4, #dcfce7);
            border: 1px solid #10b981;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 10px;
        ">
            <div style="
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
                text-align: center;
            ">
                <div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #10b981;">{summary.get('passed', 0)}</div>
                    <div style="font-size: 0.8rem; color: #059669; text-transform: uppercase; letter-spacing: 0.5px;">Passed</div>
                </div>
                <div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #ef4444;">{summary.get('failed', 0)}</div>
                    <div style="font-size: 0.8rem; color: #dc2626; text-transform: uppercase; letter-spacing: 0.5px;">Failed</div>
                </div>
            </div>
            <div style="
                margin-top: 10px;
                text-align: center;
                font-size: 0.9rem;
                color: #374151;
            ">
                COMP519 Compliance: <strong>{summary.get('comp519_compliance', 0):.1f}%</strong>
            </div>
        </div>
        
        <!-- Session Info -->
        <div style="
            background: linear-gradient(135deg, #eff6ff, #dbeafe);
            border: 1px solid #3b82f6;
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 15px;
            font-size: 0.85rem;
            color: #1e40af;
        ">
            <div style="margin-bottom: 5px;">
                <i class="fas fa-clock" style="margin-right: 6px;"></i>
                Duration: <strong>{duration:.1f}s</strong>
            </div>
            <div style="margin-bottom: 5px;">
                <i class="fas fa-list-ol" style="margin-right: 6px;"></i>
                Tests: <strong>{summary.get('total_tests', 0)}</strong>
            </div>
            <div>
                <i class="fas fa-code" style="margin-right: 6px;"></i>
                Assignment: <strong>COMP519 A4</strong>
            </div>
        </div>
        
        <!-- Action Buttons -->
        <div style="display: flex; flex-direction: column; gap: 10px;">
            <a href="/" style="
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                padding: 12px 20px;
                background: linear-gradient(135deg, #10b981, #059669);
                color: white;
                text-decoration: none;
                border-radius: 12px;
                font-weight: 600;
                font-size: 0.9rem;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
            " 
            onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 8px 25px rgba(16, 185, 129, 0.4)'"
            onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px rgba(16, 185, 129, 0.3)'">
                <i class="fas fa-home"></i>
                Test Another API
            </a>
            
            <a href="/api/download-report/{session_id}" style="
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                padding: 12px 20px;
                background: linear-gradient(135deg, #3b82f6, #2563eb);
                color: white;
                text-decoration: none;
                border-radius: 12px;
                font-weight: 600;
                font-size: 0.9rem;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
            " 
            download="comp519_{username}_api_report.html"
            onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 8px 25px rgba(59, 130, 246, 0.4)'"
            onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px rgba(59, 130, 246, 0.3)'">
                <i class="fas fa-download"></i>
                Download Report
            </a>
            
            <button onclick="exportToPDF()" style="
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                padding: 12px 20px;
                background: linear-gradient(135deg, #8b5cf6, #7c3aed);
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: 600;
                font-size: 0.9rem;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
            "
            onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 8px 25px rgba(139, 92, 246, 0.4)'"
            onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px rgba(139, 92, 246, 0.3)'">
                <i class="fas fa-file-pdf"></i>
                Print for Submission
            </a>
        </div>
        
        <!-- COMP519 Quick Navigation -->
        <div style="
            border-top: 1px solid rgba(107, 114, 128, 0.2);
            padding-top: 15px;
            margin-top: 10px;
        ">
            <div style="
                font-weight: 600;
                font-size: 0.9rem;
                color: #374151;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                gap: 6px;
            ">
                <i class="fas fa-bookmark"></i>
                Assignment Sections
            </div>
            <div style="display: flex; flex-direction: column; gap: 5px;">
                <a href="#endpoints-summary" onclick="scrollToSection('endpoints-summary')" style="
                    color: #6b7280;
                    text-decoration: none;
                    font-size: 0.85rem;
                    padding: 5px 10px;
                    border-radius: 6px;
                    transition: all 0.2s ease;
                " onmouseover="this.style.background='rgba(107, 114, 128, 0.1)'; this.style.color='#374151'"
                onmouseout="this.style.background='transparent'; this.style.color='#6b7280'">
                    🔗 API Endpoints
                </a>
                <a href="#compliance-check" onclick="scrollToSection('compliance-check')" style="
                    color: #6b7280;
                    text-decoration: none;
                    font-size: 0.85rem;
                    padding: 5px 10px;
                    border-radius: 6px;
                    transition: all 0.2s ease;
                " onmouseover="this.style.background='rgba(107, 114, 128, 0.1)'; this.style.color='#374151'"
                onmouseout="this.style.background='transparent'; this.style.color='#6b7280'">
                    ✅ Compliance Check
                </a>
                <a href="#test-results" onclick="scrollToSection('test-results')" style="
                    color: #6b7280;
                    text-decoration: none;
                    font-size: 0.85rem;
                    padding: 5px 10px;
                    border-radius: 6px;
                    transition: all 0.2s ease;
                " onmouseover="this.style.background='rgba(107, 114, 128, 0.1)'; this.style.color='#374151'"
                onmouseout="this.style.background='transparent'; this.style.color='#6b7280'">
                    📊 Detailed Results
                </a>
            </div>
        </div>
    </div>
    
    <script>
        let isNavigationCollapsed = false;
        
        function toggleNavigation() {{
            const nav = document.getElementById('report-navigation');
            const icon = nav.querySelector('button i');
            
            if (isNavigationCollapsed) {{
                nav.style.transform = 'translateX(0)';
                nav.style.opacity = '1';
                icon.className = 'fas fa-eye-slash';
                isNavigationCollapsed = false;
            }} else {{
                nav.style.transform = 'translateX(calc(100% - 60px))';
                nav.style.opacity = '0.7';
                icon.className = 'fas fa-eye';
                isNavigationCollapsed = true;
            }}
        }}
        
        function scrollToSection(sectionName) {{
            const element = document.getElementById(sectionName) || document.querySelector('.' + sectionName + '-section');
            if (element) {{
                element.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            }}
        }}
        
        function exportToPDF() {{
            const originalTitle = document.title;
            document.title = 'COMP519 Assignment 4 - API Test Report - {username}';
            
            const nav = document.getElementById('report-navigation');
            nav.style.display = 'none';
            
            window.print();
            
            setTimeout(() => {{
                nav.style.display = 'flex';
                document.title = originalTitle;
            }}, 1000);
        }}
        
        // Add Font Awesome if not already present
        if (!document.querySelector('link[href*="font-awesome"]')) {{
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css';
            document.head.appendChild(link);
        }}
        
        // Responsive behavior
        function handleResize() {{
            const nav = document.getElementById('report-navigation');
            if (window.innerWidth <= 768) {{
                nav.style.position = 'relative';
                nav.style.top = 'auto';
                nav.style.right = 'auto';
                nav.style.margin = '20px auto';
                nav.style.maxWidth = '400px';
            }} else {{
                nav.style.position = 'fixed';
                nav.style.top = '20px';
                nav.style.right = '20px';
                nav.style.margin = '0';
            }}
        }}
        
        window.addEventListener('resize', handleResize);
        document.addEventListener('DOMContentLoaded', handleResize);
    </script>
    """
    
    if '<body>' in report_html:
        report_html = report_html.replace('<body>', f'<body>{navigation_html}', 1)
    
    return report_html

@app.route('/api/download-report/<session_id>')
def download_report(session_id):
    session = test_sessions.get(session_id)
    if not session or session['status'] != 'completed':
        return jsonify({'error': 'COMP519 report not available'}), 404
    
    try:
        report_generator = ReportGenerator()
        username = session.get('username', 'unknown')
        report_path = report_generator.generate_comp519_html_report(
            session['results'], 
            username,
            session_id
        )
        
        return send_file(
            report_path, 
            as_attachment=True, 
            download_name=f'comp519_{username}_api_test_report.html'
        )
    
    except Exception as e:
        logging.error(f"Failed to download COMP519 report for session {session_id}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'COMP519 API Tester',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'active_sessions': len(test_sessions)
    })

@app.route('/api/sessions')
def list_sessions():
    sessions_info = {}
    for session_id, session in test_sessions.items():
        sessions_info[session_id] = {
            'status': session['status'],
            'progress': session['progress'],
            'start_time': session['start_time'],
            'username': session.get('username'),
            'total_tests': session.get('results', {}).get('summary', {}).get('total_tests', 0) if session.get('results') else 0
        }
    
    return jsonify({
        'total_sessions': len(test_sessions),
        'sessions': sessions_info
    })

def run_comp519_tests(session_id, html_content, username):
    session = test_sessions[session_id]
    
    try:
        session['status'] = 'running'
        session['logs'].append({
            'message': f'Starting COMP519 API validation for {username}...', 
            'type': 'info', 
            'timestamp': datetime.now().isoformat()
        })
        
        tester = COMP519APITester(
            session_id, 
            update_callback=lambda msg, type_='info': update_session_log(session_id, msg, type_)
        )
        
        session['logs'].append({
            'message': f'Testing API at: https://student.csc.liv.ac.uk/~{username}/v1', 
            'type': 'info', 
            'timestamp': datetime.now().isoformat()
        })
        session['progress'] = 10
        
        results = tester.test_api_from_html(html_content, username)
        
        session['results'] = results
        session['status'] = 'completed'
        session['progress'] = 100
        session['end_time'] = datetime.now().isoformat()
        session['logs'].append({
            'message': f'COMP519 API testing completed! Compliance: {results["summary"]["comp519_compliance"]:.1f}%', 
            'type': 'success', 
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        session['status'] = 'failed'
        session['end_time'] = datetime.now().isoformat()
        session['logs'].append({
            'message': f'COMP519 testing failed: {str(e)}', 
            'type': 'error', 
            'timestamp': datetime.now().isoformat()
        })
        session['logs'].append({
            'message': f'Error details: {error_details}', 
            'type': 'error', 
            'timestamp': datetime.now().isoformat()
        })
        
        logging.error(f"COMP519 testing failed for session {session_id}: {str(e)}")
        logging.error(f"Full traceback: {error_details}")

def update_session_log(session_id, message, type_='info'):
    if session_id in test_sessions:
        test_sessions[session_id]['logs'].append({
            'message': message,
            'type': type_,
            'timestamp': datetime.now().isoformat()
        })
        
        if 'Testing' in message and any(word in message for word in ['endpoint', 'GET', 'POST', 'PATCH', 'DELETE']):
            current_progress = test_sessions[session_id].get('progress', 10)
            test_sessions[session_id]['progress'] = min(current_progress + 4, 90)
        
        if type_ == 'error':
            logging.error(f"COMP519 Session {session_id}: {message}")
        elif type_ == 'warning':
            logging.warning(f"COMP519 Session {session_id}: {message}")
        else:
            logging.info(f"COMP519 Session {session_id}: {message}")

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html',
                         error_title="Page Not Found",
                         error_message="The requested page could not be found."), 404

@app.errorhandler(500)
def internal_error(error):
    logging.error(f"Internal server error: {str(error)}", exc_info=True)
    return render_template('error.html',
                         error_title="Internal Server Error",
                         error_message="An unexpected error occurred. Please try again later."), 500

@app.context_processor
def inject_common_vars():
    return {
        'app_name': 'TestFlow Pro - COMP519',
        'app_version': '1.0.0',
        'current_year': datetime.now().year
    }

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/comp519_app_{datetime.now().strftime("%Y%m%d")}.log'),
            logging.StreamHandler()
        ]
    )
    
    app.run(debug=True, host='0.0.0.0', port=5000)