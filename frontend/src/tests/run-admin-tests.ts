#!/usr/bin/env tsx
/**
 * Master Opaque-Box Test Runner for Admin Health Dashboard (/admin/health)
 * Executes Tier 1, Tier 2, Tier 3, Tier 4 Test Suites
 */

import * as path from 'path';
import { TestSuiteRunner } from './test-utils';
import { runTier1Tests } from './tier1-build-route.test';
import { runTier2Tests } from './tier2-boundary.test';
import { runTier3Tests } from './tier3-dynamic-state.test';
import { runTier4Tests } from './tier4-scenarios.test';
import { runTier5Tests } from './tier5-hardening.test';

async function main() {
  console.log('\n================================================================');
  console.log('  STARTING OPAQUE-BOX AUTOMATED TEST SUITE FOR /admin/health    ');
  console.log('================================================================\n');

  const runner = new TestSuiteRunner();
  // Project root is the frontend directory
  const projectRoot = path.resolve(__dirname, '..', '..');

  try {
    // Execute Tier 1: Build & Route Accessibility
    await runTier1Tests(runner, projectRoot);

    // Execute Tier 2: Boundary & Edge Cases
    await runTier2Tests(runner);

    // Execute Tier 3: Dynamic State Binding & Interactions
    await runTier3Tests(runner);

    // Execute Tier 4: Real-World Error Visualization Scenarios
    await runTier4Tests(runner);

    // Execute Tier 5: White-Box Adversarial Hardening
    await runTier5Tests(runner);

    // Output Final Summary
    const summary = runner.printSummary();

    if (!summary.success) {
      console.error('❌ Test suite failed with errors.');
      process.exit(1);
    } else {
      console.log('✨ All test tiers executed and passed successfully!');
      process.exit(0);
    }
  } catch (err) {
    console.error('💥 Fatal error occurred during test suite execution:', err);
    process.exit(1);
  }
}

main();
