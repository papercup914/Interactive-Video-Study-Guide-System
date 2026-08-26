/**
 * Empirical Stress Test Suite for Milestone M1 (Infrastructure & Data Layer)
 * Focus: generateMockHealthData dynamic generator, type robustness, and edge cases
 */

import { generateMockHealthData, UseAdminHealthOptions } from '../hooks/useAdminHealth';
import { ErrorCategory, LogLevel } from '../types/adminHealth';

interface TestResult {
  name: string;
  passed: boolean;
  details: string;
  error?: string;
}

const results: TestResult[] = [];

function assert(condition: boolean, testName: string, details: string) {
  if (condition) {
    results.push({ name: testName, passed: true, details });
    console.log(`[PASS] ${testName}: ${details}`);
  } else {
    results.push({ name: testName, passed: false, details, error: `Assertion failed` });
    console.error(`[FAIL] ${testName}: ${details}`);
  }
}

console.log('=== Starting M1 Empirical Stress Tests ===\n');

// ------------------------------------------------------------------
// Test Group 1: Default / Null / Undefined Options
// ------------------------------------------------------------------
try {
  const d1 = generateMockHealthData();
  assert(d1.logs.length === 10, 'Default Call (no args)', `Returned ${d1.logs.length} logs (expected 10)`);
  assert(d1.timeSeries.length === 12, 'Default TimeSeries 24h', `Returned ${d1.timeSeries.length} points (expected 12)`);
  assert(d1.summary.totalLogs === 10, 'Default Summary TotalLogs', `Summary totalLogs = ${d1.summary.totalLogs}`);

  const d2 = generateMockHealthData({});
  assert(d2.logs.length === 10, 'Empty Options ({})', `Returned ${d2.logs.length} logs`);
} catch (err: any) {
  assert(false, 'Default/Null Options', `Threw error: ${err.message}`);
}

// ------------------------------------------------------------------
// Test Group 2: Special Characters in Search Query
// ------------------------------------------------------------------
const specialQueries = [
  '[critical]',
  '.*',
  '\\',
  '?',
  '$',
  '(',
  '<script>alert(1)</script>',
  '"\'',
  '안녕',
  '🚨',
  "' OR 1=1 --",
  '   ',
  '   job-9842   ',
];

specialQueries.forEach((sq) => {
  try {
    const res = generateMockHealthData({ searchQuery: sq });
    assert(
      Array.isArray(res.logs),
      `Special Query: "${sq}"`,
      `Handled safely without crash. Returned ${res.logs.length} logs.`
    );
  } catch (err: any) {
    assert(false, `Special Query: "${sq}"`, `CRASHED with error: ${err.message}`);
  }
});

// ------------------------------------------------------------------
// Test Group 3: Non-String / Malformed Search Query Types
// ------------------------------------------------------------------
const malformedQueries = [123, true, false, {}, [], null];

malformedQueries.forEach((mq) => {
  try {
    const res = generateMockHealthData({ searchQuery: mq as any });
    assert(
      Array.isArray(res.logs),
      `Malformed SearchQuery: ${JSON.stringify(mq)}`,
      `Handled safely without crash. Returned ${res.logs.length} logs.`
    );
  } catch (err: any) {
    assert(false, `Malformed SearchQuery: ${JSON.stringify(mq)}`, `CRASHED with error: ${err.message}`);
  }
});

// ------------------------------------------------------------------
// Test Group 4: Category Filter Corner Cases & Zero Matches
// ------------------------------------------------------------------
try {
  // Test filtering by category with zero logs matching
  const zeroMatchRes = generateMockHealthData({
    category: 'LLM Generation Error',
    searchQuery: 'NONEXISTENT_QUERY_XYZ_123456',
  });

  assert(
    zeroMatchRes.logs.length === 0,
    'Zero Match Search - Logs Array',
    `Returned ${zeroMatchRes.logs.length} logs (expected 0)`
  );
  assert(
    zeroMatchRes.summary.totalLogs === 0,
    'Zero Match Search - Summary TotalLogs',
    `Summary totalLogs = ${zeroMatchRes.summary.totalLogs} (expected 0)`
  );

  // CRITICAL CHECK: Category Breakdown consistency when filteredLogs is 0
  const totalCatCountInBreakdown = zeroMatchRes.categoryBreakdown.reduce((sum, c) => sum + c.count, 0);
  console.log(`[DIAGNOSTIC] Zero Match categoryBreakdown total sum of counts: ${totalCatCountInBreakdown}`);

  const breakdownMatchesLogs = totalCatCountInBreakdown === zeroMatchRes.logs.length;
  assert(
    breakdownMatchesLogs,
    'Category Breakdown Consistency on Zero Matches',
    `Breakdown sum (${totalCatCountInBreakdown}) matches filtered logs count (${zeroMatchRes.logs.length})`
  );
} catch (err: any) {
  assert(false, 'Category Filter Zero Match', `Threw error: ${err.message}`);
}

// ------------------------------------------------------------------
// Test Group 5: Invalid Time Ranges
// ------------------------------------------------------------------
const invalidRanges = ['invalid', '1h', '999d', '', null as any, undefined, {} as any];

invalidRanges.forEach((tr) => {
  try {
    const res = generateMockHealthData({ timeRange: tr });
    assert(
      Array.isArray(res.timeSeries) && res.timeSeries.length > 0,
      `Invalid TimeRange: ${JSON.stringify(tr)}`,
      `Fallback timeSeries points generated: ${res.timeSeries.length}`
    );
  } catch (err: any) {
    assert(false, `Invalid TimeRange: ${JSON.stringify(tr)}`, `CRASHED with error: ${err.message}`);
  }
});

// ------------------------------------------------------------------
// Test Group 6: Level Filter Corner Cases
// ------------------------------------------------------------------
const levels: (LogLevel | 'ALL' | 'UNKNOWN')[] = ['info', 'warning', 'error', 'critical', 'ALL', 'UNKNOWN' as any];

levels.forEach((lvl) => {
  try {
    const res = generateMockHealthData({ level: lvl as any });
    assert(
      Array.isArray(res.logs),
      `Level Filter: "${lvl}"`,
      `Returned ${res.logs.length} logs`
    );
  } catch (err: any) {
    assert(false, `Level Filter: "${lvl}"`, `CRASHED with error: ${err.message}`);
  }
});

// ------------------------------------------------------------------
// Test Summary
// ------------------------------------------------------------------
console.log('\n=== M1 Stress Test Summary ===');
const passedCount = results.filter((r) => r.passed).length;
const failedCount = results.filter((r) => !r.passed).length;
console.log(`Total: ${results.length} | Passed: ${passedCount} | Failed: ${failedCount}`);

if (failedCount > 0) {
  console.log('\nFailed Tests:');
  results.filter((r) => !r.passed).forEach((r) => console.log(`- ${r.name}: ${r.details} (${r.error})`));
} else {
  console.log('\nALL TESTS PASSED!');
}
