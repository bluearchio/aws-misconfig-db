/**
 * Basic Usage Example for AWS Misconfiguration Database (Node.js)
 *
 * This script demonstrates how to load and query the database in Node.js
 */

const fs = require('fs');
const path = require('path');

/**
 * Load the complete misconfiguration database
 */
function loadDatabase(filePath = '../../data/all-misconfigs.json') {
  const fullPath = path.join(__dirname, filePath);
  const data = fs.readFileSync(fullPath, 'utf8');
  return JSON.parse(data);
}

/**
 * Load misconfigurations for a specific AWS service
 */
function loadServiceData(service, dataDir = '../../data/by-service') {
  const fullPath = path.join(__dirname, dataDir, `${service}.json`);
  const data = fs.readFileSync(fullPath, 'utf8');
  return JSON.parse(data);
}

/**
 * Filter misconfigurations by risk type
 */
function filterByRisk(misconfigs, riskType) {
  return misconfigs.filter(m =>
    (m.risk_detail || '').includes(riskType)
  );
}

/**
 * Filter misconfigurations by priority
 */
function filterByPriority(misconfigs, maxPriority = 1) {
  return misconfigs.filter(m =>
    m.build_priority !== null && m.build_priority <= maxPriority
  );
}

/**
 * Filter misconfigurations by AWS service
 */
function filterByService(misconfigs, service) {
  return misconfigs.filter(m => m.service_name === service);
}

/**
 * Search for keyword in scenarios
 */
function searchScenarios(misconfigs, keyword) {
  const keywordLower = keyword.toLowerCase();
  return misconfigs.filter(m =>
    (m.scenario || '').toLowerCase().includes(keywordLower) ||
    (m.recommendation_description_detailed || '').toLowerCase().includes(keywordLower)
  );
}

/**
 * Get cost optimization opportunities sorted by value
 */
function getCostOptimizations(misconfigs, minValue = 2) {
  const costItems = filterByRisk(misconfigs, 'cost');
  const highValue = costItems.filter(m =>
    m.action_value !== null && m.action_value >= minValue
  );

  return highValue.sort((a, b) => {
    const effortA = a.effort_level || 99;
    const effortB = b.effort_level || 99;
    const valueA = a.action_value || 0;
    const valueB = b.action_value || 0;

    if (effortA !== effortB) {
      return effortA - effortB;
    }
    return valueB - valueA;
  });
}

/**
 * Get critical security misconfigurations
 */
function getSecurityCritical(misconfigs) {
  const securityItems = filterByRisk(misconfigs, 'security');
  return securityItems.filter(m => (m.risk_value || 0) >= 2);
}

/**
 * Pretty print a misconfiguration entry
 */
function printMisconfiguration(misconfig, detailed = false) {
  console.log(`\nID: ${misconfig.id}`);
  console.log(`Service: ${misconfig.service_name}`);
  console.log(`Scenario: ${misconfig.scenario}`);
  console.log(`Risk: ${misconfig.risk_detail} (Priority: ${misconfig.build_priority})`);
  console.log(`Recommendation: ${misconfig.recommendation_action}`);

  if (detailed) {
    if (misconfig.alert_criteria) {
      console.log(`\nAlert Criteria: ${misconfig.alert_criteria}`);
    }
    if (misconfig.recommendation_description_detailed) {
      console.log(`\nDetailed Description: ${misconfig.recommendation_description_detailed}`);
    }
    if (misconfig.references && misconfig.references.length > 0) {
      console.log('\nReferences:');
      misconfig.references.forEach(ref => console.log(`  - ${ref}`));
    }
  }
}

function main() {
  // Example 1: Load and explore the database
  console.log('='.repeat(60));
  console.log('Example 1: Load Database');
  console.log('='.repeat(60));

  const db = loadDatabase();
  console.log(`Total misconfigurations: ${db.total_count}`);
  console.log(`Services covered: ${db.services.length}`);
  console.log(`Categories: ${db.categories.join(', ')}`);

  // Example 2: Filter by risk type
  console.log('\n' + '='.repeat(60));
  console.log('Example 2: Security Misconfigurations');
  console.log('='.repeat(60));

  const securityIssues = filterByRisk(db.misconfigurations, 'security');
  console.log(`Found ${securityIssues.length} security-related misconfigurations`);

  securityIssues.slice(0, 3).forEach(m => printMisconfiguration(m));

  // Example 3: High-priority items
  console.log('\n' + '='.repeat(60));
  console.log('Example 3: High Priority Issues');
  console.log('='.repeat(60));

  const highPriority = filterByPriority(db.misconfigurations, 0);
  console.log(`Found ${highPriority.length} critical priority misconfigurations`);

  // Example 4: Cost optimizations
  console.log('\n' + '='.repeat(60));
  console.log('Example 4: Best Cost Optimizations (High Value, Low Effort)');
  console.log('='.repeat(60));

  const costOpts = getCostOptimizations(db.misconfigurations, 2);
  console.log(`Found ${costOpts.length} high-value cost optimizations`);

  costOpts.slice(0, 5).forEach(m => {
    const effort = m.effort_level || '?';
    const value = m.action_value || '?';
    console.log(`\n- ${m.scenario} (Effort: ${effort}, Value: ${value})`);
    console.log(`  Recommendation: ${m.recommendation_action}`);
  });

  // Example 5: Service-specific query
  console.log('\n' + '='.repeat(60));
  console.log('Example 5: EC2-Specific Misconfigurations');
  console.log('='.repeat(60));

  const ec2Data = loadServiceData('ec2');
  console.log(`Found ${ec2Data.count} EC2 misconfigurations`);

  // Example 6: Search by keyword
  console.log('\n' + '='.repeat(60));
  console.log('Example 6: Search for \'encryption\'');
  console.log('='.repeat(60));

  const encryptionItems = searchScenarios(db.misconfigurations, 'encryption');
  console.log(`Found ${encryptionItems.length} items related to encryption`);

  encryptionItems.slice(0, 3).forEach(m => {
    console.log(`\n- ${m.service_name}: ${m.scenario}`);
  });
}

// Run if executed directly
if (require.main === module) {
  main();
}

// Export functions for use as a module
module.exports = {
  loadDatabase,
  loadServiceData,
  filterByRisk,
  filterByPriority,
  filterByService,
  searchScenarios,
  getCostOptimizations,
  getSecurityCritical
};
