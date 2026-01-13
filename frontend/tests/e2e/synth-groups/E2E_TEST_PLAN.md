# E2E Test Plan - Synth Groups Feature

## Overview
End-to-end tests for the custom synth groups feature, covering the complete user flow from creating groups to using them in experiments.

## Test Scenarios

### 1. Create Basic Synth Group
**User Story**: As a PM, I want to create a basic synth group with just a name
- Navigate to synth groups page
- Click "Create Group" button
- Fill in group name
- Submit form
- Verify group appears in list

### 2. Create Synth Group with Custom Distributions
**User Story**: As a PM, I want to create a group with custom demographic distributions
- Navigate to synth groups page
- Click "Create Group" button
- Fill in group name and description
- Adjust age distribution sliders
- Adjust education distribution sliders
- Adjust disability configuration
- Adjust family composition sliders
- Select domain expertise preset
- Submit form (may take several seconds)
- Verify group appears in list with correct synth count

### 3. View Synth Group Details
**User Story**: As a PM, I want to see the details of a synth group including its synths
- Navigate to synth groups list
- Click on a group card
- Verify group details are displayed
- Verify list of synths is shown
- Verify config is displayed (if present)

### 4. Use Synth Group in Experiment
**User Story**: As a PM, I want to link an experiment to a specific synth group
- Navigate to experiments page
- Click "New Experiment" button
- Fill in experiment details
- Select synth group from dropdown
- Submit form
- Verify experiment is created with correct group
- Navigate to experiment detail
- Verify synth group is displayed

### 5. Delete Synth Group
**User Story**: As a PM, I want to delete a synth group that's no longer needed
- Navigate to synth groups list
- Click on a group
- Click delete button
- Confirm deletion
- Verify group is removed from list

### 6. Filter Synths by Group
**User Story**: As a PM, I want to see only synths from a specific group
- Navigate to synth groups page
- Select a group
- View synths in that group
- Verify all synths belong to the selected group

### 7. Distribution Slider Normalization
**User Story**: As a PM, I want sliders to auto-adjust to sum to 100%
- Open create group modal
- Adjust one age slider
- Verify other sliders auto-adjust
- Verify total sums to ~100%

### 8. Reset Distribution to Defaults
**User Story**: As a PM, I want to reset distributions to IBGE defaults
- Open create group modal
- Adjust distributions
- Click reset button for a distribution
- Verify distribution returns to default values

## Test Data Requirements

### Test Groups
- **Default Group**: Always present (grp_00000001)
- **Basic Test Group**: Name only, no synths
- **Custom Distribution Group**: With custom distributions, 10-50 synths
- **Large Group**: 500 synths for performance testing

### Test Experiments
- **Default Group Experiment**: Uses default group
- **Custom Group Experiment**: Uses custom group
- **Multiple Experiments**: Different groups for testing

## Assertions

### Visual Assertions
- ✓ Modal opens correctly
- ✓ Form fields are visible
- ✓ Sliders render properly
- ✓ Distribution totals display correctly
- ✓ Loading states show during synth generation
- ✓ Toast notifications appear on success/error

### Data Assertions
- ✓ Group created with correct name
- ✓ Group has correct synth count
- ✓ Config stored correctly in database
- ✓ Experiment linked to correct group
- ✓ Synths have correct group_id

### Navigation Assertions
- ✓ Redirects to list after creation
- ✓ Can navigate to group detail
- ✓ Can navigate from group to experiments
- ✓ Back button works correctly

## Performance Considerations

- Creating groups with 500 synths may take 5-10 seconds
- Use appropriate timeouts for long operations
- Test with realistic data volumes

## Error Scenarios

### Validation Errors
- Empty group name
- Invalid distribution sums
- n_synths out of range (< 1 or > 1000)

### Network Errors
- API timeout during synth generation
- 404 for non-existent group
- 422 for invalid config

## Browser Support
- Chrome (primary)
- Firefox
- Safari (if available)

## Test Execution

```bash
# Run all synth groups E2E tests
npx playwright test tests/e2e/synth-groups/

# Run specific test file
npx playwright test tests/e2e/synth-groups/create-group.spec.ts

# Run with UI mode for debugging
npx playwright test --ui

# Run in headed mode
npx playwright test --headed
```

## Test Maintenance

- Update selectors if UI changes
- Update test data if business rules change
- Keep tests independent (no shared state)
- Clean up test data after each test
- Use fixture data consistently
