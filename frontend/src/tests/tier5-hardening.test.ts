/**
 * Tier 5 White-Box Adversarial Hardening Test Suite
 * Focus: Unhandled edge case code paths, state conditions, null detail fallbacks,
 * extreme numeric bounds, multi-byte Unicode search queries, and component prop resilience.
 */

import { generateMockHealthData, UseAdminHealthOptions } from '../hooks/useAdminHealth';
import { assertEquals, assertGreaterThanOrEqual, assertIsTrue, assertNotNull, TestSuiteRunner } from './test-utils';
import { ErrorCategory, LogLevel, SystemHealthSummary, SystemLogEntry } from '../types/adminHealth';

export async function runTier5Tests(runner: TestSuiteRunner): Promise<void> {
  runner.setTier('Tier 5: White-Box Adversarial Hardening');

  // Test 5.1: Null Details & Missing Optional Log Fields Safety
  await runner.runTest('T5.1: Logs with null details, null jobId, null statusCode process cleanly without TypeError', () => {
    // Generate base mock data and verify log entries with null details/jobId
    const data = generateMockHealthData();
    const logWithNullDetails = data.logs.find((l) => l.details === null);
    assertNotNull(logWithNullDetails, 'Mock data should contain at least one log with null details (log-008)');
    assertEquals(logWithNullDetails?.details, null, 'Details field should be null');

    const logWithNullJobId = data.logs.find((l) => l.jobId === null);
    assertNotNull(logWithNullJobId, 'Mock data should contain at least one log with null jobId');
    assertEquals(logWithNullJobId?.jobId, null, 'jobId field should be null');

    // Search query matching against null fields
    const searchResultNullJob = generateMockHealthData({ searchQuery: 'null' });
    assertIsTrue(Array.isArray(searchResultNullJob.logs), 'Search result with "null" string returns valid logs array');

    const searchResultEmpty = generateMockHealthData({ searchQuery: 'routine' });
    assertEquals(searchResultEmpty.logs.length, 1, 'Should find log-008 which has null details');
  });

  // Test 5.2: Multi-byte Unicode, Emoji, and Regex Special Characters in Search Query
  await runner.runTest('T5.2: Search filter resilience with Unicode (Korean, CJK), Emoji (🔥🚨), control chars, and Regex symbols', () => {
    const adversarialQueries = [
      '시스템 에러 테스트',           // Korean text
      '🔥🚨 CRITICAL_BURST 🚨🔥',   // Emoji
      'job-9842[.*+?^${}()|[\\]\\\\]',// Regex special characters
      'hello\x00world\x1b',         // Control characters
      'A'.repeat(1000),             // Extreme length query (1000 chars)
    ];

    adversarialQueries.forEach((query) => {
      const data = generateMockHealthData({ searchQuery: query });
      assertIsTrue(Array.isArray(data.logs), `Query "${query.slice(0, 30)}..." must return valid array`);
      assertIsTrue(typeof data.summary.errorRate === 'number', 'Summary errorRate must remain valid number');
    });
  });

  // Test 5.3: Single Log Category Breakdown Math & Zero-Division Defense
  await runner.runTest('T5.3: Category breakdown distribution math under filtered single-entry and zero-entry datasets', () => {
    // Filter specifically by 'Auth Error' which has 1 entry
    const authData = generateMockHealthData({ category: 'Auth Error' });
    assertEquals(authData.logs.length, 1, 'Auth Error filter should return exactly 1 log entry');

    const authCategoryItem = authData.categoryBreakdown.find((c) => c.category === 'Auth Error');
    assertNotNull(authCategoryItem, 'Auth Error breakdown item must exist');
    assertEquals(authCategoryItem?.count, 1, 'Auth Error count should be 1');
    assertEquals(authCategoryItem?.percentage, 100, 'Auth Error percentage should be 100% when it is the sole filtered log');

    // Other categories in breakdown should have count = 0 and percentage = 0
    authData.categoryBreakdown.forEach((c) => {
      if (c.category !== 'Auth Error') {
        assertEquals(c.count, 0, `Category ${c.category} count must be 0`);
        assertEquals(c.percentage, 0, `Category ${c.category} percentage must be 0%`);
      }
    });

    // Verify sum of percentages is exactly 100%
    const totalPercentage = authData.categoryBreakdown.reduce((sum, item) => sum + item.percentage, 0);
    assertEquals(Number(totalPercentage.toFixed(1)), 100, 'Total percentage sum must equal 100%');
  });

  // Test 5.4: System Health Status Boundary State Machine
  await runner.runTest('T5.4: State machine verification for system status boundaries (Healthy vs Degraded vs Critical)', () => {
    // Case A: Default state with unresolved critical log (log-001) -> 'Critical'
    const defaultData = generateMockHealthData();
    assertEquals(defaultData.summary.systemStatus, 'Critical', 'Default state has unresolved critical error so status must be Critical');

    // Case B: Filter by level 'info' (0 errors, 0 warnings, 0 critical) -> 'Healthy'
    const infoData = generateMockHealthData({ level: 'info' });
    assertEquals(infoData.summary.systemStatus, 'Healthy', 'Info-only filter has 0 errors/warnings so status must be Healthy');
    assertEquals(infoData.summary.errorRate, 0, 'Info-only filter error rate must be 0%');

    // Case C: Filter by category 'Render Warning' (0 errors, 2 warnings) -> 'Healthy'
    const warnData = generateMockHealthData({ category: 'Render Warning' });
    assertEquals(warnData.summary.systemStatus, 'Healthy', 'Warning-only filter with <= 3 errors must be Healthy');
    assertEquals(warnData.summary.errorRate, 0, 'Warning-only filter error rate must be 0%');
  });

  // Test 5.5: Options Boundary & Default Parameters Safety
  await runner.runTest('T5.5: generateMockHealthData handles empty options {}, undefined, or partial options gracefully', () => {
    const dataNullOptions = generateMockHealthData(undefined);
    assertNotNull(dataNullOptions.summary, 'Summary must be defined for undefined options');
    assertGreaterThanOrEqual(dataNullOptions.timeSeries.length, 12, 'Default timeRange 24h must yield 12 points');

    const dataEmptyOptions = generateMockHealthData({});
    assertNotNull(dataEmptyOptions.summary, 'Summary must be defined for empty options object');

    const dataPartialOptions = generateMockHealthData({ timeRange: '7d' });
    assertEquals(dataPartialOptions.timeSeries.length, 7, 'Partial options with 7d must yield 7 points');
  });

  // Test 5.6: Extreme Time Ranges & Large Point Calculations
  await runner.runTest('T5.6: Time series points calculations maintain valid structure across all supported time ranges', () => {
    const ranges: ('24h' | '7d' | '30d')[] = ['24h', '7d', '30d'];

    ranges.forEach((range) => {
      const data = generateMockHealthData({ timeRange: range });
      data.timeSeries.forEach((pt) => {
        assertIsTrue(pt.errorCount >= 0, 'errorCount must be non-negative');
        assertIsTrue(pt.warningCount >= 0, 'warningCount must be non-negative');
        assertIsTrue(pt.infoCount >= 0, 'infoCount must be non-negative');
        assertEquals(pt.totalCount, pt.errorCount + pt.warningCount + pt.infoCount, 'totalCount must equal sum of counts');
        assertIsTrue(typeof pt.formattedTime === 'string' && pt.formattedTime.length > 0, 'formattedTime must be non-empty string');
      });
    });
  });

  // Test 5.7: Component Prop Interface Contracts & Null Safety Checks
  await runner.runTest('T5.7: Verify data structure guarantees for direct component prop consumption', () => {
    const data = generateMockHealthData();

    // 1. HealthStatCards summary prop contract
    const summary: SystemHealthSummary = data.summary;
    assertIsTrue(typeof summary.totalErrors === 'number', 'summary.totalErrors must be number');
    assertIsTrue(typeof summary.errorRate === 'number', 'summary.errorRate must be number');
    assertIsTrue(typeof summary.totalWarnings === 'number', 'summary.totalWarnings must be number');
    assertIsTrue(typeof summary.avgLatencyMs === 'number', 'summary.avgLatencyMs must be number');
    assertIsTrue(['Healthy', 'Degraded', 'Critical'].includes(summary.systemStatus), 'summary.systemStatus must be valid enum');

    // 2. ErrorTrendChart data prop contract
    assertIsTrue(Array.isArray(data.timeSeries), 'timeSeries must be array');

    // 3. ErrorTypeBreakdownChart data prop contract
    assertIsTrue(Array.isArray(data.categoryBreakdown), 'categoryBreakdown must be array');
    data.categoryBreakdown.forEach((item) => {
      assertIsTrue(typeof item.color === 'string' && item.color.startsWith('#'), 'Color must be hex color string');
    });

    // 4. ErrorLogInspector logs prop contract
    assertIsTrue(Array.isArray(data.logs), 'logs must be array');
    data.logs.forEach((log) => {
      assertIsTrue(['critical', 'error', 'warning', 'info'].includes(log.level), 'Log level must be valid enum');
      assertIsTrue(typeof log.message === 'string', 'Log message must be string');
    });
  });

  // Test 5.8: Special Character Job ID Matching in Log Entries
  await runner.runTest('T5.8: Special character job ID search query substring matching', () => {
    const data = generateMockHealthData({ searchQuery: 'job-9842' });
    assertEquals(data.logs.length, 1, 'Search for job-9842 should return exactly 1 log');
    assertEquals(data.logs[0].id, 'log-001', 'Log log-001 must match job-9842');

    const dataHyphen = generateMockHealthData({ searchQuery: 'job-' });
    assertGreaterThanOrEqual(dataHyphen.logs.length, 5, 'Search for "job-" should match multiple job IDs');
  });
}
