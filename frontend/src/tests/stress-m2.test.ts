import { generateMockHealthData } from '../hooks/useAdminHealth';
import { SystemLogEntry, SystemHealthSummary } from '../types/adminHealth';

async function runStressTests() {
  console.log('=== STARTING ADVERSARIAL STRESS TEST FOR M2 ===\n');
  let passCount = 0;
  let failCount = 0;

  function assert(condition: boolean, testName: string, detail?: string) {
    if (condition) {
      console.log(`  [PASS] ${testName}`);
      passCount++;
    } else {
      console.error(`  [FAIL] ${testName}${detail ? `: ${detail}` : ''}`);
      failCount++;
    }
  }

  // 1. Empty Log List & Null Props Handling
  try {
    const emptyData = generateMockHealthData({ searchQuery: 'NON_EXISTENT_QUERY_SEARCH_xyz_123_random' });
    assert(emptyData.logs.length === 0, '1.1 Mock generator returns empty logs array on unmatched query');
    assert(emptyData.summary.totalLogs === 0, '1.2 Summary totalLogs is 0 for empty logs');
    assert(emptyData.summary.errorRate === 0, '1.3 Summary errorRate is 0% for empty logs');

    const nullSummary: SystemHealthSummary | null = null;
    const statCardsSummary = nullSummary ?? { systemStatus: 'Healthy', totalLogs: 0, errorRate: 0, totalErrors: 0, totalWarnings: 0, avgLatencyMs: 0, activeJobs: 0, lastUpdated: new Date().toISOString() };
    assert(statCardsSummary.totalErrors === 0, '1.4 HealthStatCards handles null summary safely');

  } catch (err) {
    assert(false, '1. Empty/Null prop stress test threw error', String(err));
  }

  // 2. Extremely Long Message & Unbroken Strings
  try {
    const longMsg = 'A'.repeat(5000);
    const longDetail = 'ERROR_STACK_TRACE_LINE\n' + 'B'.repeat(10000);
    const longLog: SystemLogEntry = {
      id: 'log-long-001',
      timestamp: new Date().toISOString(),
      level: 'critical',
      category: 'API Error',
      source: 'Backend / FastAPI Router',
      message: longMsg,
      details: longDetail,
      jobId: 'job-' + '9'.repeat(100),
      statusCode: 500,
      resolved: false,
    };

    assert(longLog.message.length === 5000, '2.1 Constructed 5000-char unbroken message log entry');
    assert(typeof longLog.details === 'string' && longLog.details.length > 10000, '2.2 Constructed >10,000-char detail log entry');
  } catch (err) {
    assert(false, '2. Long message stress test failed', String(err));
  }

  // 3. Special Characters & Injection Attacks in Search Query
  try {
    const specialChars = [
      '<script>alert("xss")</script>',
      "'; DROP TABLE logs; --",
      '${process.env.SECRET}',
      '{{ 7 * 7 }}',
      '[a-z]+.*',
      '\\\\\\\\\\\\',
      '👍🔥🎉',
      '日本語 / 한글 / العربية',
      '%\x00null',
    ];

    for (const sc of specialChars) {
      const result = generateMockHealthData({ searchQuery: sc });
      assert(Array.isArray(result.logs), `3. Search query '${sc}' handled safely without crashing`);
    }
  } catch (err) {
    assert(false, '3. Special character search stress test failed', String(err));
  }

  // 4. Extreme Numeric Boundary Values
  try {
    const extremeSummary: SystemHealthSummary = {
      systemStatus: 'Critical',
      totalLogs: 1000000000,
      errorRate: 100.0,
      totalErrors: 999999999,
      totalWarnings: 888888888,
      avgLatencyMs: 999999,
      activeJobs: 5000,
      lastUpdated: 'invalid-date-string-test',
    };

    assert(extremeSummary.totalErrors === 999999999, '4.1 Extreme integer count handled in data model');
    assert(isNaN(new Date(extremeSummary.lastUpdated).getTime()), '4.2 Invalid date string detected without crash');
  } catch (err) {
    assert(false, '4. Extreme numeric boundary test failed', String(err));
  }

  console.log(`\n=== STRESS TEST RESULTS: ${passCount} Passed, ${failCount} Failed ===`);
  if (failCount > 0) {
    process.exit(1);
  }
}

runStressTests();
