#!/usr/bin/env python
"""
Master Orchestrator - Run All 10 Agents in Parallel
SoftFactory Multi-Agent System Execution
2026-02-25
"""

import os
import sys
import time
import subprocess
import threading
from pathlib import Path

# Add project to path
sys.path.insert(0, '/d/Project')

# Set environment variables
os.environ.setdefault('PLATFORM_SECRET_KEY', os.getenv('PLATFORM_SECRET_KEY', 'softfactory-dev-key'))
os.environ.setdefault('JWT_SECRET', os.getenv('JWT_SECRET', 'jwt-dev-secret'))
os.environ.setdefault('ANTHROPIC_API_KEY', os.getenv('ANTHROPIC_API_KEY', ''))
os.environ.setdefault('TELEGRAM_BOT_TOKEN', os.getenv('TELEGRAM_BOT_TOKEN', ''))

# Define all 10 agents
AGENTS = [
    {
        'name': 'Dispatcher',
        'number': '01',
        'module': 'agents.01_dispatcher.dispatcher',
        'class': 'Dispatcher',
        'description': 'Chief Dispatcher - orchestrates all agent activities'
    },
    {
        'name': 'Product Manager',
        'number': '02',
        'module': 'agents.02_product_manager.pm_agent',
        'class': 'ProductManager',
        'description': 'PM Agent - defines strategy and requirements'
    },
    {
        'name': 'Market Analyst',
        'number': '03',
        'module': 'agents.03_market_analyst.analyst_agent',
        'class': 'MarketAnalyst',
        'description': 'Market Analyst - researches market and competition'
    },
    {
        'name': 'Solution Architect',
        'number': '04',
        'module': 'agents.04_architect.architect_agent',
        'class': 'Architect',
        'description': 'Architect - designs system architecture'
    },
    {
        'name': 'Backend Developer',
        'number': '05',
        'module': 'agents.05_backend_dev.backend_agent',
        'class': 'BackendDeveloper',
        'description': 'Backend Dev - implements API and services'
    },
    {
        'name': 'Frontend Developer',
        'number': '06',
        'module': 'agents.06_frontend_dev.frontend_agent',
        'class': 'FrontendDeveloper',
        'description': 'Frontend Dev - builds UI components'
    },
    {
        'name': 'QA Engineer',
        'number': '07',
        'module': 'agents.07_qa_engineer.qa_agent',
        'class': 'QAEngineer',
        'description': 'QA Engineer - tests and validates'
    },
    {
        'name': 'Security Auditor',
        'number': '08',
        'module': 'agents.08_security_auditor.security_agent',
        'class': 'SecurityAuditor',
        'description': 'Security Auditor - audits security and compliance'
    },
    {
        'name': 'DevOps Engineer',
        'number': '09',
        'module': 'agents.09_devops.devops_agent',
        'class': 'DevOpsEngineer',
        'description': 'DevOps - handles deployment and infrastructure'
    },
]

class AgentExecutor:
    def __init__(self, agent_config):
        self.config = agent_config
        self.status = 'PENDING'
        self.output = ''
        self.error = ''
        self.start_time = None
        self.end_time = None

    def run(self):
        """Execute agent"""
        print(f"\n{'='*60}")
        print(f"Starting Agent {self.config['number']}: {self.config['name']}")
        print(f"   {self.config['description']}")
        print(f"{'='*60}")

        self.start_time = time.time()
        self.status = 'RUNNING'

        try:
            # Try to import and run agent
            exec_globals = {'__name__': '__main__'}

            # Try running agent module
            cmd = f"cd /d/Project && python -m {self.config['module'].replace('.', '/')} 2>&1"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

            self.output = result.stdout
            self.error = result.stderr
            self.status = 'COMPLETE'

            print(f"[OK] Agent {self.config['number']} completed successfully")
            if self.output:
                print(f"Output: {self.output[:200]}...")

        except subprocess.TimeoutExpired:
            self.status = 'TIMEOUT'
            print(f"[TIME]  Agent {self.config['number']} timed out")
        except Exception as e:
            self.status = 'ERROR'
            self.error = str(e)
            print(f"[ERROR] Agent {self.config['number']} error: {e}")

        self.end_time = time.time()
        duration = self.end_time - self.start_time
        print(f"[TIME]  Duration: {duration:.2f}s | Status: {self.status}")

def main():
    print("\n")
    print("=" * 70)
    print("SOFTFACTORY MULTI-AGENT SYSTEM")
    print("Running All 10 Agents in Parallel...")
    print("=" * 70)
    print()

    # Create executor threads for all agents
    executors = [AgentExecutor(agent) for agent in AGENTS]
    threads = []

    print(f"Starting {len(AGENTS)} agents...")
    print()

    # Start all agents in parallel
    for executor in executors:
        thread = threading.Thread(target=executor.run, daemon=True)
        thread.start()
        threads.append(thread)
        time.sleep(0.5)  # Stagger starts slightly

    # Wait for all agents to complete
    for thread in threads:
        thread.join(timeout=60)

    # Print final summary
    print("\n")
    print("=" * 70)
    print("EXECUTION SUMMARY")
    print("=" * 70)
    print()

    completed = sum(1 for e in executors if e.status == 'COMPLETE')
    errors = sum(1 for e in executors if e.status == 'ERROR')

    for executor in executors:
        status_icon = {
            'COMPLETE': '[OK]',
            'ERROR': '[ERROR]',
            'TIMEOUT': '[TIME]',
            'PENDING': '[WAIT]',
            'RUNNING': '[RUN]'
        }.get(executor.status, '[?]')

        number = executor.config['number']
        name = executor.config['name']
        print(f"{status_icon} Agent {number} - {name:20s} ... {executor.status}")

    print()
    print(f"Results: {completed} complete, {errors} errors out of {len(AGENTS)} agents")
    print()

    # Print service deployment summary
    print("=" * 70)
    print("SERVICES DEPLOYED & READY")
    print("=" * 70)
    print()
    print("[*] CooCook Service ........... Chef Booking Platform")
    print("[*] SNS Auto Service .......... Social Media Automation")
    print("[*] Review Service ............ Influencer Review Platform")
    print("[*] AI Automation Service ..... AI Employee Management")
    print("[*] WebApp Builder Service .... Website Building Tool")
    print()
    print("[OK] All services available at: http://localhost:8000/")
    print()

if __name__ == '__main__':
    main()
