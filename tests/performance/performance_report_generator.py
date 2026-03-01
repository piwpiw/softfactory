"""
Performance Report Generator
Analyzes profiling and load test results, generates recommendations
"""

import json
from datetime import datetime
from typing import Dict, List, Tuple
from pathlib import Path


class PerformanceAnalyzer:
    """Analyze performance metrics and generate insights"""

    # Performance thresholds (in milliseconds)
    THRESHOLDS = {
        'excellent': 50,      # < 50ms
        'good': 100,          # < 100ms
        'acceptable': 200,    # < 200ms
        'poor': 500,          # < 500ms
        'critical': 1000,     # > 1000ms
    }

    @staticmethod
    def categorize_response_time(ms: float) -> Tuple[str, str]:
        """Categorize response time with emoji indicator"""
        if ms < PerformanceAnalyzer.THRESHOLDS['excellent']:
            return '🟢', 'EXCELLENT'
        elif ms < PerformanceAnalyzer.THRESHOLDS['good']:
            return '🟢', 'GOOD'
        elif ms < PerformanceAnalyzer.THRESHOLDS['acceptable']:
            return '🟡', 'ACCEPTABLE'
        elif ms < PerformanceAnalyzer.THRESHOLDS['poor']:
            return '🔴', 'POOR'
        else:
            return '⛔', 'CRITICAL'

    @staticmethod
    def analyze_endpoint(endpoint_stats: Dict) -> Dict:
        """Analyze single endpoint statistics"""

        mean_ms = float(endpoint_stats.get('mean_ms', 0))
        p95_ms = float(endpoint_stats.get('p95_ms', 0) or endpoint_stats.get('p95_ms', '0'))
        success_rate = endpoint_stats.get('success_rate', '0%')

        emoji, category = PerformanceAnalyzer.categorize_response_time(mean_ms)

        return {
            'endpoint': endpoint_stats['endpoint'],
            'mean_response_time_ms': mean_ms,
            'p95_response_time_ms': p95_ms,
            'performance_category': category,
            'emoji': emoji,
            'success_rate': success_rate,
        }

    @staticmethod
    def identify_bottlenecks(results: Dict) -> List[Dict]:
        """Identify performance bottlenecks"""

        bottlenecks = []

        # 1. Slow endpoints (mean > 100ms)
        for endpoint, stats in results.get('baseline_profiling', {}).items():
            mean_ms = float(stats.get('mean_ms', 0))
            if mean_ms > PerformanceAnalyzer.THRESHOLDS['good']:
                bottlenecks.append({
                    'type': 'SLOW_ENDPOINT',
                    'severity': 'HIGH' if mean_ms > 500 else 'MEDIUM',
                    'endpoint': endpoint,
                    'metric': f"Response time: {mean_ms:.2f}ms",
                    'recommendation': 'Add caching or optimize database queries'
                })

        # 2. High variance in response times
        for endpoint, stats in results.get('baseline_profiling', {}).items():
            stdev = stats.get('stdev_ms', '0')
            if stdev != 'N/A':
                stdev_val = float(stdev)
                mean_ms = float(stats.get('mean_ms', 0))
                if stdev_val > mean_ms * 0.5:  # Stdev > 50% of mean
                    bottlenecks.append({
                        'type': 'INCONSISTENT_PERFORMANCE',
                        'severity': 'MEDIUM',
                        'endpoint': endpoint,
                        'metric': f"Std Dev: {stdev_val:.2f}ms (Mean: {mean_ms:.2f}ms)",
                        'recommendation': 'Investigate variable load patterns or resource contention'
                    })

        # 3. Low success rates
        for endpoint, stats in results.get('baseline_profiling', {}).items():
            success_rate = float(stats.get('success_rate', '100').rstrip('%'))
            if success_rate < 95:
                bottlenecks.append({
                    'type': 'RELIABILITY_ISSUE',
                    'severity': 'CRITICAL',
                    'endpoint': endpoint,
                    'metric': f"Success rate: {success_rate:.1f}%",
                    'recommendation': 'Check error logs and stabilize endpoint'
                })

        # 4. Load test failures
        for load_test in results.get('load_tests', []):
            success_rate = float(load_test.get('success_rate', '100').rstrip('%'))
            if success_rate < 90:
                bottlenecks.append({
                    'type': 'LOAD_HANDLING_ISSUE',
                    'severity': 'CRITICAL',
                    'endpoint': f"{load_test['endpoint']} ({load_test['concurrent_requests']} concurrent)",
                    'metric': f"Success rate: {success_rate:.1f}%",
                    'recommendation': 'Increase connection pool size or add load balancing'
                })

        # 5. Throughput analysis
        for load_test in results.get('load_tests', []):
            throughput = float(load_test.get('throughput_rps', 0))
            if throughput < 10:  # Less than 10 RPS
                bottlenecks.append({
                    'type': 'LOW_THROUGHPUT',
                    'severity': 'MEDIUM',
                    'endpoint': f"{load_test['endpoint']} ({load_test['concurrent_requests']} concurrent)",
                    'metric': f"Throughput: {throughput:.2f} req/sec",
                    'recommendation': 'Profile database connections and consider connection pooling'
                })

        return sorted(bottlenecks, key=lambda x: {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2}.get(x['severity'], 3))

    @staticmethod
    def generate_recommendations(bottlenecks: List[Dict], results: Dict) -> List[Dict]:
        """Generate optimization recommendations based on analysis"""

        recommendations = []

        # 1. Caching recommendations
        slow_endpoints = [b for b in bottlenecks if b['type'] == 'SLOW_ENDPOINT']
        if slow_endpoints:
            recommendations.append({
                'priority': 'P0_CRITICAL',
                'category': 'CACHING',
                'title': 'Implement Flask-Caching',
                'description': 'Add in-memory or Redis caching for frequently accessed endpoints',
                'affected_endpoints': [e['endpoint'] for e in slow_endpoints],
                'expected_improvement': '50-80% reduction in response time',
                'implementation_effort': 'LOW (2-4 hours)',
                'code_snippet': '''
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/api/coocook/chefs')
@cache.cached(timeout=300, query_string=True)
def get_chefs():
    # Endpoint implementation
    pass
                '''
            })

        # 2. Database optimization
        recommendations.append({
            'priority': 'P0_CRITICAL',
            'category': 'DATABASE',
            'title': 'Add Database Indexes',
            'description': 'Create indexes on frequently filtered columns',
            'affected_queries': [
                'chefs.is_active (chef listing)',
                'chefs.cuisine_type (cuisine filtering)',
                'bookings.user_id (user bookings)',
                'bookings.chef_id (chef bookings)',
            ],
            'expected_improvement': '30-70% faster queries',
            'implementation_effort': 'LOW (1-2 hours)',
            'sql_queries': '''
CREATE INDEX idx_chefs_is_active ON chefs(is_active);
CREATE INDEX idx_chefs_cuisine ON chefs(cuisine_type);
CREATE INDEX idx_bookings_user ON bookings(user_id);
CREATE INDEX idx_bookings_chef ON bookings(chef_id);
            '''
        })

        # 3. Query optimization (N+1)
        recommendations.append({
            'priority': 'P1_HIGH',
            'category': 'QUERY_OPTIMIZATION',
            'title': 'Fix N+1 Query Problems',
            'description': 'Use eager loading to fetch related data in single query',
            'current_pattern': '''
chefs = Chef.query.all()
for chef in chefs:
    bookings = chef.bookings  # ← Separate query for each chef!
            ''',
            'optimized_pattern': '''
from sqlalchemy.orm import joinedload

chefs = Chef.query.options(joinedload('bookings')).all()
for chef in chefs:
    bookings = chef.bookings  # ← Already loaded!
            ''',
            'expected_improvement': '50-90% fewer database queries',
            'implementation_effort': 'MEDIUM (4-8 hours)',
        })

        # 4. Connection pooling
        recommendations.append({
            'priority': 'P1_HIGH',
            'category': 'CONNECTION_POOL',
            'title': 'Configure Database Connection Pooling',
            'description': 'Use SQLAlchemy connection pool to handle concurrent requests',
            'current_issue': 'Default pool may not handle 50+ concurrent connections',
            'solution': '''
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 20,
    'pool_recycle': 3600,
    'pool_pre_ping': True,  # Verify connections before use
    'max_overflow': 40,
}
            ''',
            'expected_improvement': '40-60% improvement under load',
            'implementation_effort': 'LOW (1 hour)',
        })

        # 5. Response compression
        recommendations.append({
            'priority': 'P2_MEDIUM',
            'category': 'COMPRESSION',
            'title': 'Enable Gzip Compression',
            'description': 'Compress JSON responses to reduce bandwidth',
            'implementation': '''
from flask_compress import Compress

Compress(app)  # Automatically compresses responses > 500 bytes
            ''',
            'expected_improvement': '60-80% reduction in response size',
            'implementation_effort': 'LOW (30 minutes)',
        })

        # 6. Pagination defaults
        recommendations.append({
            'priority': 'P2_MEDIUM',
            'category': 'API_DESIGN',
            'title': 'Optimize Pagination',
            'description': 'Ensure pagination limits prevent large dataset transfers',
            'current': 'per_page=12 (good)',
            'recommendation': 'Enforce max_per_page=50 to prevent abuse',
            'implementation_effort': 'LOW (30 minutes)',
        })

        # 7. Monitoring
        recommendations.append({
            'priority': 'P3_LOW',
            'category': 'MONITORING',
            'title': 'Implement Performance Monitoring',
            'description': 'Add APM tools to continuously track performance',
            'tools': ['New Relic', 'DataDog', 'Sentry', 'Prometheus'],
            'expected_benefit': 'Early detection of performance regressions',
            'implementation_effort': 'MEDIUM (8-16 hours)',
        })

        return recommendations


class ReportGenerator:
    """Generate markdown performance report"""

    @staticmethod
    def generate_markdown_report(results: Dict, output_path: str = None) -> str:
        """Generate comprehensive markdown report"""

        analyzer = PerformanceAnalyzer()
        bottlenecks = analyzer.identify_bottlenecks(results)
        recommendations = analyzer.generate_recommendations(bottlenecks, results)

        report = []
        report.append("# SoftFactory API Performance Report")
        report.append("")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        report.append("---")
        report.append("")

        # Executive Summary
        report.append("## Executive Summary")
        report.append("")
        total_endpoints = len(results.get('baseline_profiling', {}))
        total_issues = len(bottlenecks)
        critical_issues = len([b for b in bottlenecks if b['severity'] == 'CRITICAL'])

        report.append(f"- **Total Endpoints Tested**: {total_endpoints}")
        report.append(f"- **Performance Issues Found**: {total_issues}")
        report.append(f"- **Critical Issues**: {critical_issues}")
        report.append(f"- **Status**: {'🟢 GOOD' if critical_issues == 0 else '🔴 NEEDS ATTENTION'}")
        report.append("")

        # Baseline Performance Metrics
        report.append("## 1. Baseline Performance Metrics")
        report.append("")
        report.append("| Endpoint | Method | Mean (ms) | P95 (ms) | P99 (ms) | Status |")
        report.append("|----------|--------|----------|---------|---------|--------|")

        for endpoint, stats in results.get('baseline_profiling', {}).items():
            mean_ms = float(stats.get('mean_ms', 0))
            p95_ms = stats.get('p95_ms', 'N/A')
            p99_ms = stats.get('p99_ms', 'N/A')
            emoji, category = analyzer.categorize_response_time(mean_ms)

            report.append(
                f"| {endpoint} | {stats.get('method', 'GET')} | {mean_ms:.2f} | "
                f"{p95_ms} | {p99_ms} | {emoji} {category} |"
            )

        report.append("")

        # Load Test Results
        report.append("## 2. Load Test Results")
        report.append("")

        for load_test in results.get('load_tests', []):
            report.append(f"### {load_test['endpoint']} ({load_test['concurrent_requests']} concurrent requests)")
            report.append("")
            report.append(f"- **Throughput**: {load_test.get('throughput_rps', 'N/A')} req/sec")
            report.append(f"- **Success Rate**: {load_test.get('success_rate', 'N/A')}")
            report.append(f"- **Mean Response Time**: {load_test.get('mean_ms', 'N/A')} ms")
            report.append(f"- **P95 Response Time**: {load_test.get('p95_ms', 'N/A')} ms")
            report.append(f"- **Failed Requests**: {load_test.get('failed_requests', 0)}")
            report.append("")

        # Bottleneck Analysis
        report.append("## 3. Bottleneck Analysis")
        report.append("")

        if bottlenecks:
            for i, bottleneck in enumerate(bottlenecks, 1):
                severity_emoji = {'CRITICAL': '⛔', 'HIGH': '🔴', 'MEDIUM': '🟡'}.get(bottleneck['severity'], '🟢')
                report.append(f"### {i}. {bottleneck['type']} {severity_emoji}")
                report.append(f"**Severity**: {bottleneck['severity']}")
                report.append(f"**Endpoint**: `{bottleneck.get('endpoint', 'N/A')}`")
                report.append(f"**Metric**: {bottleneck.get('metric', 'N/A')}")
                report.append(f"**Recommendation**: {bottleneck.get('recommendation', 'See recommendations section')}")
                report.append("")
        else:
            report.append("✅ No critical bottlenecks detected!")
            report.append("")

        # Recommendations
        report.append("## 4. Optimization Recommendations")
        report.append("")

        for i, rec in enumerate(recommendations, 1):
            priority_emoji = {'P0_CRITICAL': '🔴', 'P1_HIGH': '🟠', 'P2_MEDIUM': '🟡', 'P3_LOW': '🟢'}.get(rec['priority'], '')

            report.append(f"### {i}. {rec['title']} {priority_emoji}")
            report.append(f"**Priority**: {rec['priority'].replace('_', ' ')}")
            report.append(f"**Category**: {rec['category']}")
            report.append(f"**Description**: {rec['description']}")

            if 'expected_improvement' in rec:
                report.append(f"**Expected Improvement**: {rec['expected_improvement']}")

            if 'implementation_effort' in rec:
                report.append(f"**Implementation Effort**: {rec['implementation_effort']}")

            if 'code_snippet' in rec:
                report.append(f"\n**Implementation**:")
                report.append(f"```python")
                report.append(rec['code_snippet'].strip())
                report.append(f"```\n")

            if 'sql_queries' in rec:
                report.append(f"\n**SQL**:")
                report.append(f"```sql")
                report.append(rec['sql_queries'].strip())
                report.append(f"```\n")

            if 'affected_endpoints' in rec:
                report.append(f"**Affected Endpoints**: {', '.join(rec['affected_endpoints'])}")
                report.append("")

            if 'affected_queries' in rec:
                report.append(f"**Affected Queries**:")
                for query in rec['affected_queries']:
                    report.append(f"  - {query}")
                report.append("")

        # Implementation Roadmap
        report.append("## 5. Implementation Roadmap")
        report.append("")
        report.append("### Phase 1 (Week 1) - Quick Wins")
        report.append("- [ ] Add Flask-Caching decorator to GET endpoints")
        report.append("- [ ] Enable Gzip compression")
        report.append("- [ ] Configure connection pooling")
        report.append("")
        report.append("### Phase 2 (Week 2) - Database Optimization")
        report.append("- [ ] Create database indexes")
        report.append("- [ ] Fix N+1 query problems with eager loading")
        report.append("- [ ] Run load tests again")
        report.append("")
        report.append("### Phase 3 (Week 3+) - Monitoring & Tuning")
        report.append("- [ ] Implement APM monitoring")
        report.append("- [ ] Continuous performance testing in CI/CD")
        report.append("- [ ] Set up alerts for performance regressions")
        report.append("")

        # Performance Benchmarks
        report.append("## 6. Target Performance Benchmarks")
        report.append("")
        report.append("| Metric | Target | Current | Status |")
        report.append("|--------|--------|---------|--------|")
        report.append("| GET /api/coocook/chefs mean | < 50ms | TBD | TBD |")
        report.append("| POST /api/coocook/bookings mean | < 100ms | TBD | TBD |")
        report.append("| 50 concurrent requests success | > 99% | TBD | TBD |")
        report.append("| 100 concurrent requests success | > 95% | TBD | TBD |")
        report.append("| 500 concurrent requests throughput | > 50 req/s | TBD | TBD |")
        report.append("")

        # Appendix
        report.append("## 7. Technical Details")
        report.append("")
        report.append("### Database Indexes")
        report.append("")
        report.append("The following indexes should be created for optimal performance:")
        report.append("")
        for rec in recommendations:
            if rec['category'] == 'DATABASE' and 'sql_queries' in rec:
                report.append(rec['sql_queries'].strip())
        report.append("")

        report.append("### Cache Strategy")
        report.append("")
        report.append("```python")
        report.append("STATIC_CACHE_TIMEOUT = 3600    # 1 hour - Products, scenarios")
        report.append("LIST_CACHE_TIMEOUT = 300       # 5 min - Chef lists, campaigns")
        report.append("DETAIL_CACHE_TIMEOUT = 600     # 10 min - Chef details")
        report.append("USER_CACHE_TIMEOUT = 60        # 1 min - User-specific data")
        report.append("```")
        report.append("")

        report.append("---")
        report.append("")
        report.append("*Report generated by SoftFactory Performance Analysis System*")
        report.append("")

        full_report = "\n".join(report)

        # Save to file if path provided
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(full_report)
            print(f"✅ Report saved to {output_path}")

        return full_report


if __name__ == "__main__":
    # Example usage
    print("Performance Report Generator")
    print("=" * 60)

    # Load example results
    try:
        with open('D:/Project/performance_baseline.json', 'r') as f:
            results = json.load(f)

        report = ReportGenerator.generate_markdown_report(
            results,
            output_path='D:/Project/docs/PERFORMANCE_REPORT.md'
        )

        print("\n" + report[:500] + "...")

    except FileNotFoundError:
        print("⚠️  performance_baseline.json not found. Run profiler.py first.")
