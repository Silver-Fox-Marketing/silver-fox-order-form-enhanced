# Git Workflow for Multi-Machine Development

## Overview
This project is actively developed on two machines:
- **Mac Mini** (main workstation at Silver Fox)
- **MacBook Pro M2** (home development)

## Daily Workflow

### Starting a Session

**ALWAYS** start each coding session with:
```bash
git pull origin main
```

This ensures you have the latest changes from the other machine.

### During Development

1. **Regular Commits**: Commit frequently with descriptive messages
   ```bash
   git add .
   git commit -m "feat: enhance Honda Frontenac scraper with complete pagination

   - Added complete inventory extraction with pagination
   - Enhanced data extraction to match complete_data.csv format  
   - Added Honda-specific navigation functions
   - Target: Extract 50+ vehicles like Columbia Honda success

   🤖 Generated with Claude Code
   
   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

2. **Push After Major Milestones**: Push immediately after:
   - Completing a scraper enhancement
   - Fixing a major bug
   - Adding new functionality
   - Before ending a session

   ```bash
   git push origin main
   ```

### Major Milestone Examples
- **Scraper Enhancements**: Any scraper that achieves complete inventory extraction
- **New Working Scrapers**: Successfully created and tested scrapers  
- **Architecture Changes**: Updates to base classes or core functionality
- **Documentation Updates**: README, workflow, or API documentation changes
- **Bug Fixes**: Critical fixes that affect multiple scrapers

### Commit Message Format
Use conventional commits with Claude Code attribution:

```
type(scope): brief description

- Detailed bullet points of changes
- Include performance metrics when available
- Reference successful patterns used

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types:**
- `feat`: New features or enhancements
- `fix`: Bug fixes
- `docs`: Documentation updates
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

## Current Project Status

### Scraper Development Progress
- ✅ **Complete Inventory Extraction**: Implemented pagination for full dealership inventories
- ✅ **Proven Patterns**: Columbia Honda (52+ vehicles), Bommarito Cadillac (264+ vehicles)
- ✅ **Anti-Bot Measures**: Chrome driver with stealth configurations
- ✅ **Complete Data Format**: All scrapers match complete_data.csv structure (21 columns)

### Recent Completions
- Honda Frontenac enhanced with complete pagination
- BMW St. Louis with advanced anti-bot bypass
- Columbia Honda with proven pagination (52+ vehicles)
- Multiple dealership scrapers with complete inventory extraction

### Next Steps
- Continue one-by-one scraper optimization
- Verify all scrapers produce complete inventories
- Regular commit/push for machine synchronization

## Machine Synchronization Rules

### Mac Mini → MacBook Pro
1. Complete work on Mac Mini
2. Commit and push changes
3. On MacBook Pro: `git pull origin main` before starting

### MacBook Pro → Mac Mini  
1. Complete work on MacBook Pro
2. Commit and push changes
3. On Mac Mini: `git pull origin main` before starting

### Session Handoff Protocol
1. **Ending Session**: Always push completed work
2. **Starting Session**: Always pull latest changes
3. **Conflict Prevention**: Never work on same files simultaneously
4. **Communication**: Use detailed commit messages for context

## Emergency Scenarios

### Merge Conflicts
```bash
# Pull and resolve conflicts
git pull origin main

# Edit conflicted files
# Remove conflict markers (<<<<<<< ======= >>>>>>>)
# Keep the correct version

# Commit resolution
git add .
git commit -m "resolve: merge conflict between machines"
git push origin main
```

### Lost Changes
```bash
# Check recent commits
git log --oneline -10

# Recover specific commit
git checkout <commit-hash> -- <file>
```

### Unsaved Work Transfer
```bash
# Stash current work
git stash save "WIP: current development state"
git push origin main

# On other machine
git pull origin main
git stash pop
```

## Success Metrics

### Scraper Quality Standards
- **Complete Inventory**: Must extract hundreds of vehicles (not just first page)
- **Pagination Working**: Multiple pages successfully navigated
- **Data Quality**: All 21 CSV columns populated
- **Anti-Bot Success**: Chrome driver bypasses protection
- **Performance**: Reasonable extraction speed with rate limiting

### Recent Achievements
- **Columbia Honda**: 52+ vehicles with 4 vehicles/page × 14+ pages
- **Bommarito Cadillac**: 264+ vehicles across 11+ pages (24 vehicles/page)
- **Complete Data Format**: All scrapers now produce proper CSV structure

This workflow ensures seamless development across both machines while maintaining code quality and project momentum.