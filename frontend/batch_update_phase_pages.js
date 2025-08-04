const fs = require('fs');
const path = require('path');

// Configuration for remaining pages
const pagesToUpdate = [
  { 
    file: 'NewRequestInfoPage.tsx',
    phaseName: 'Request for Information',
    searchPattern: /getRequestInfoSteps\(\)\.map\(/,
    functionName: 'getRequestInfoSteps'
  },
  { 
    file: 'TestExecutionPage.tsx',
    phaseName: 'Test Execution',
    searchPattern: /getTestExecutionSteps\(\)\.map\(/,
    functionName: 'getTestExecutionSteps'
  },
  { 
    file: 'ObservationManagementEnhanced.tsx',
    phaseName: 'Observation Management',
    searchPattern: /getObservationSteps\(\)\.map\(/,
    functionName: 'getObservationSteps'
  },
  { 
    file: 'TestReportPage.tsx',
    phaseName: 'Finalize Test Report',
    searchPattern: /getFinalizeReportSteps\(\)\.map\(/,
    functionName: 'getFinalizeReportSteps'
  }
];

const addDynamicActivityCards = (filePath, phaseName, searchPattern, functionName) => {
  let content = fs.readFileSync(filePath, 'utf8');
  
  // Add import if not already present
  if (!content.includes("import { DynamicActivityCards }")) {
    const importRegex = /import { usePhaseStatus[^}]+} from '\.\.\/\.\.\/hooks\/useUnifiedStatus';/;
    content = content.replace(importRegex, (match) => {
      return match + "\nimport { DynamicActivityCards } from '../../components/phase/DynamicActivityCards';";
    });
  }
  
  // Find where the steps are mapped and replace with conditional rendering
  const mapRegex = new RegExp(`(\\s*)\\{${functionName}\\(\\)\\.map\\(\\(step, index\\) => \\([\\s\\S]*?\\)\\)\\}`, 'g');
  
  content = content.replace(mapRegex, (match, indent) => {
    const dynamicCards = `${indent}{unifiedPhaseStatus?.activities ? (
${indent}  <DynamicActivityCards
${indent}    activities={unifiedPhaseStatus.activities}
${indent}    cycleId={cycleIdNum}
${indent}    reportId={reportIdNum}
${indent}    phaseName="${phaseName}"
${indent}    onActivityAction={handleActivityAction}
${indent}  />
${indent}) : (
${indent}  // Fallback to hardcoded steps
${match}
${indent})}`;
    
    return dynamicCards;
  });
  
  // Add handleActivityAction function if not present
  if (!content.includes('handleActivityAction')) {
    // Find a good place to insert - after handleCompletePhase or similar
    const insertRegex = /(\s*};\s*\n)(\s*const\s+\w+\s*=)/;
    const handleActivityAction = `

  const handleActivityAction = async (activity: any, action: string) => {
    try {
      setLoading(true);
      if (action === 'start') {
        // Handle activity start
        await apiClient.post(\`/activity-states/transition\`, {
          cycle_id: cycleIdNum,
          report_id: reportIdNum,
          phase_name: '${phaseName}',
          activity_name: activity.name,
          target_state: 'In Progress'
        });
        showToast.success(\`Started activity: \${activity.name}\`);
      } else if (action === 'complete') {
        // Handle activity completion
        await apiClient.post(\`/activity-states/transition\`, {
          cycle_id: cycleIdNum,
          report_id: reportIdNum,
          phase_name: '${phaseName}',
          activity_name: activity.name,
          target_state: 'Completed'
        });
        showToast.success(\`Completed activity: \${activity.name}\`);
      }
      await refetchStatus();
    } catch (error: any) {
      console.error(\`Error \${action}ing activity:\`, error);
      showToast.error(\`Failed to \${action} activity\`);
    } finally {
      setLoading(false);
    }
  };
`;
    
    content = content.replace(insertRegex, (match, ending, nextConst) => {
      return ending + handleActivityAction + '\n' + nextConst;
    });
  }
  
  fs.writeFileSync(filePath, content);
  console.log(`✅ Updated ${path.basename(filePath)}`);
};

// Process each page
pagesToUpdate.forEach(page => {
  const filePath = path.join(__dirname, 'src/pages/phases', page.file);
  if (fs.existsSync(filePath)) {
    try {
      addDynamicActivityCards(filePath, page.phaseName, page.searchPattern, page.functionName);
    } catch (error) {
      console.error(`❌ Error updating ${page.file}:`, error.message);
    }
  } else {
    console.log(`❓ File not found: ${page.file}`);
  }
});

console.log('\n✨ Batch update complete!');