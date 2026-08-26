/**
 * Automated Test Runner Utilities & Assertion Library for Admin Health Dashboard
 * Opaque-Box Test Framework
 */

export interface TestResult {
  tier: string;
  name: string;
  passed: boolean;
  durationMs: number;
  error?: Error | string;
  details?: string;
}

export class TestSuiteRunner {
  private results: TestResult[] = [];
  private currentTier: string = 'General';

  public setTier(tierName: string): void {
    this.currentTier = tierName;
  }

  public async runTest(name: string, fn: () => void | Promise<void>): Promise<boolean> {
    const start = Date.now();
    try {
      await fn();
      const durationMs = Date.now() - start;
      this.results.push({
        tier: this.currentTier,
        name,
        passed: true,
        durationMs,
      });
      console.log(`  \x1b[32m✔ PASS\x1b[0m [${this.currentTier}] ${name} (${durationMs}ms)`);
      return true;
    } catch (err: unknown) {
      const durationMs = Date.now() - start;
      const error = err instanceof Error ? err : String(err);
      this.results.push({
        tier: this.currentTier,
        name,
        passed: false,
        durationMs,
        error,
      });
      console.log(`  \x1b[31m✘ FAIL\x1b[0m [${this.currentTier}] ${name} (${durationMs}ms)`);
      if (err instanceof Error && err.stack) {
        console.log(`    \x1b[33mError details: ${err.message}\x1b[0m`);
      }
      return false;
    }
  }

  public getResults(): TestResult[] {
    return this.results;
  }

  public printSummary(): { total: number; passed: number; failed: number; success: boolean } {
    const total = this.results.length;
    const passed = this.results.filter((r) => r.passed).length;
    const failed = total - passed;
    const success = failed === 0;

    console.log('\n================================================================');
    console.log('         ADMIN HEALTH DASHBOARD OPAQUE-BOX TEST SUMMARY          ');
    console.log('================================================================');

    const tiers = Array.from(new Set(this.results.map((r) => r.tier)));
    tiers.forEach((t) => {
      const tierResults = this.results.filter((r) => r.tier === t);
      const tierPassed = tierResults.filter((r) => r.passed).length;
      const statusSymbol = tierPassed === tierResults.length ? '\x1b[32m[PASS]\x1b[0m' : '\x1b[31m[FAIL]\x1b[0m';
      console.log(`${statusSymbol} ${t}: ${tierPassed}/${tierResults.length} passed`);
    });

    console.log('----------------------------------------------------------------');
    if (success) {
      console.log(`\x1b[32mOVERALL STATUS: SUCCESS (${passed}/${total} Test Cases Passed)\x1b[0m`);
    } else {
      console.log(`\x1b[31mOVERALL STATUS: FAILURE (${failed}/${total} Test Cases Failed)\x1b[0m`);
    }
    console.log('================================================================\n');

    return { total, passed, failed, success };
  }
}

// Assertion Helpers
export function assertEquals<T>(actual: T, expected: T, message?: string): void {
  if (actual !== expected) {
    throw new Error(message || `Assertion Failed: Expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
  }
}

export function assertIsTrue(condition: boolean, message?: string): void {
  if (!condition) {
    throw new Error(message || 'Assertion Failed: Condition is false');
  }
}

export function assertNotNull<T>(val: T | null | undefined, message?: string): T {
  if (val === null || val === undefined) {
    throw new Error(message || 'Assertion Failed: Value is null or undefined');
  }
  return val;
}

export function assertGreaterThanOrEqual(actual: number, expected: number, message?: string): void {
  if (actual < expected) {
    throw new Error(message || `Assertion Failed: Expected ${actual} >= ${expected}`);
  }
}
