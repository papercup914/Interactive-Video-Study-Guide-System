/**
 * Tier 3 Test Suite: Dynamic State Binding & Interaction Tests
 * Focus: Severity filtering, Category selection, Search filtering, Timestamp refresh action, Calculation integrity
 */

import { generateMockHealthData } from '../hooks/useAdminHealth';
import { assertEquals, assertGreaterThanOrEqual, assertIsTrue, TestSuiteRunner } from './test-utils';

export async function runTier3Tests(runner: TestSuiteRunner): Promise<void> {
  runner.setTier('Tier 3: Dynamic State Binding & Interaction Tests');

  // Test 3.1: Filtering logs by severity level ('critical')
  await runner.runTest('T3.1: Dynamic filtering by severity level "critical"', () => {
    const data = generateMockHealthData({ level: 'critical' });
    assertGreaterThanOrEqual(data.logs.length, 1, 'Must contain at least 1 critical log in mock dataset');
    data.logs.forEach((log) => {
      assertEquals(log.level, 'critical', 'Filtered log entry level must be critical');
    });
  });

  // Test 3.2: Filtering logs by category ('LLM Generation Error')
  await runner.runTest('T3.2: Dynamic category selection filter "LLM Generation Error"', () => {
    const data = generateMockHealthData({ category: 'LLM Generation Error' });
    assertGreaterThanOrEqual(data.logs.length, 1, 'Must contain at least 1 LLM Generation Error log entry');
    data.logs.forEach((log) => {
      assertEquals(log.category, 'LLM Generation Error', 'Filtered log category must match LLM Generation Error');
    });
  });

  // Test 3.3: Interactive search filter by substring matching
  await runner.runTest('T3.3: Live search query matching substring "whisper"', () => {
    const data = generateMockHealthData({ searchQuery: 'whisper' });
    assertGreaterThanOrEqual(data.logs.length, 1, 'Must match log entry containing "whisper"');
    data.logs.forEach((log) => {
      const matchInMsg = log.message.toLowerCase().includes('whisper');
      const matchInDetails = (log.details || '').toLowerCase().includes('whisper');
      const matchInSource = log.source.toLowerCase().includes('whisper');
      assertIsTrue(matchInMsg || matchInDetails || matchInSource, 'Log entry must contain matching substring "whisper"');
    });
  });

  // Test 3.4: Refresh action updates lastUpdated timestamp ISO string
  await runner.runTest('T3.4: Dynamic refresh action produces fresh ISO timestamp in lastUpdated', async () => {
    const data1 = generateMockHealthData();
    // Short wait to ensure time difference
    await new Promise((resolve) => setTimeout(resolve, 20));
    const data2 = generateMockHealthData();

    assertIsTrue(Boolean(data1.summary.lastUpdated), 'lastUpdated must be non-empty ISO string');
    assertIsTrue(Boolean(data2.summary.lastUpdated), 'lastUpdated must be non-empty ISO string');
    const time1 = new Date(data1.summary.lastUpdated).getTime();
    const time2 = new Date(data2.summary.lastUpdated).getTime();
    assertIsTrue(time2 >= time1, 'Subsequent data refresh timestamp must be greater than or equal to previous');
  });

  // Test 3.5: Mathematical Integrity of System Health Summary Metrics
  await runner.runTest('T3.5: System summary mathematical relation integrity (totalLogs, errorRate)', () => {
    const data = generateMockHealthData();
    const computedErrors = data.logs.filter((l) => l.level === 'error' || l.level === 'critical').length;
    const computedWarnings = data.logs.filter((l) => l.level === 'warning').length;

    assertEquals(data.summary.totalLogs, data.logs.length, 'summary.totalLogs must equal data.logs.length');
    assertEquals(data.summary.totalErrors, computedErrors, 'summary.totalErrors must equal count of error/critical logs');
    assertEquals(data.summary.totalWarnings, computedWarnings, 'summary.totalWarnings must equal count of warning logs');

    const expectedRate = data.logs.length > 0 ? Number(((computedErrors / data.logs.length) * 100).toFixed(1)) : 0;
    assertEquals(data.summary.errorRate, expectedRate, 'summary.errorRate calculation matches expectation');
  });

  // Test 3.6: Category Breakdown Donut Chart Data Calculations
  await runner.runTest('T3.6: Category breakdown chart metrics sum integrity (percentages sum to ~100%)', () => {
    const data = generateMockHealthData();
    assertGreaterThanOrEqual(data.categoryBreakdown.length, 7, 'Must have breakdown items for all 7 error categories');

    const totalPct = data.categoryBreakdown.reduce((sum, item) => sum + item.percentage, 0);
    // Floating point rounding tolerance check
    assertIsTrue(totalPct >= 99.0 && totalPct <= 101.0, `Total category percentage sum must be ~100% (got ${totalPct}%)`);
  });

  // Test 3.7: Time-Series Error Frequency Chart Formatting
  await runner.runTest('T3.7: Time-series error frequency points schema & formattedTime', () => {
    const data = generateMockHealthData({ timeRange: '24h' });
    data.timeSeries.forEach((pt) => {
      assertIsTrue(typeof pt.timestamp === 'string', 'TimeSeriesPoint timestamp must be string');
      assertIsTrue(typeof pt.formattedTime === 'string', 'TimeSeriesPoint formattedTime must be string');
      assertIsTrue(pt.totalCount === pt.errorCount + pt.warningCount + pt.infoCount, 'totalCount must equal sum of error + warning + info');
    });
  });
}
