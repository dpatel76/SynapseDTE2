# Enhanced Phase Box Layout

## Visual Organization (Top to Bottom)

### Row 1: Header
- **Left**: Phase number chip + Phase name
- **Right**: Status badge(s) - Primary status + risk indicators (Overdue/At Risk)

### Row 2: Start Dates
- **Left**: "Start:" label
- **Right**: "Planned Date / Actual Date" (or "Not Started")

### Row 3: End Dates  
- **Left**: "End:" label
- **Right**: "Planned Date / Actual Date" (or "Not Started")

### Row 4: Duration (if started)
- **Left**: "Duration:" label
- **Right**: Calculated elapsed time (e.g., "5 days", "Today")

### Row 5: Progress Bar (if not "Not Started")
- Shows completion percentage with visual progress bar

### Row 6: Days Remaining (if "In Progress")
- Shows remaining time or overdue status

### Row 7: Metrics (if available)
- Compact format: "Items: 3/10 (30%)"

## Key Features

### Date Formatting
- **Compact Format**: "Jun 22" instead of full dates
- **Color Coding**: 
  - Planned dates: Regular text weight
  - Actual dates: Green color when present, gray when "Not Started"

### Status Indicators
- **Primary Status**: Not Started, In Progress, Complete
- **Risk Indicators**: Overdue (red), At Risk (orange)
- **Small chips**: Consistent 20px height, readable fonts

### Smart Visibility
- **Duration**: Only shown for phases that have started
- **Progress**: Only shown for active/completed phases  
- **Days Remaining**: Only shown for in-progress phases
- **Metrics**: Only shown when data is available

### Layout Consistency
- **Min Height**: 200px for uniform card sizing
- **Responsive**: 3×3 grid on medium+ screens, 2 columns on small, 1 on mobile
- **Hover Effects**: Subtle lift animation on hover

## Example Display

```
Phase 1  Planning & Analysis                    [Complete]

Start:                              Jun 22 / Jun 22
End:                                Jun 25 / Jun 24  
Duration:                                    2 days
Progress: ████████████████████████████████████ 100%
Items:                                      5/5 (100%)
```