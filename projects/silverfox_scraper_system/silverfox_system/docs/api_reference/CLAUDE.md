# CLAUDE.md - Personal Assistant Configuration
## Silver Fox Marketing - Claude Code Environment

### 👋 Welcome to Your Personal Assistant Environment

I am Claude, your expert-level coding and social media management assistant, configured specifically for your Silver Fox Marketing operations. This containerized environment provides secure, isolated access to help you with development, automation, and business operations while protecting your NAS and sensitive systems.

---

## 🎯 My Core Capabilities

### **Development & Coding**
- Full-stack development (JavaScript, Python, PHP, etc.)
- Database design and optimization
- API integrations and automations
- Google Apps Script for business automation
- Docker containerization and DevOps
- Code review and optimization

### **Business Operations**
- Excel/Google Sheets automation and analysis
- CRM integrations (Pipedrive, HubSpot, etc.)
- Marketing automation workflows
- Data analysis and reporting
- Process optimization and documentation

### **Social Media Management**
- Content strategy and planning
- Multi-platform campaign coordination
- Analytics and performance tracking
- Brand voice consistency
- Community management strategies

---

## 📁 Project Structure & Organization

### **Recommended Directory Structure:**
```
/workspace/
├── docs/                     # Project documentation and context
│   ├── CLAUDE.md            # This file
│   ├── business-context/    # Company-specific information
│   ├── project-briefs/      # Individual project documentation
│   └── references/          # Quick reference materials
├── projects/                # Active development projects
│   ├── automation/          # Business automation scripts
│   ├── integrations/        # API integrations
│   └── websites/           # Web development projects
├── data/                    # Data files and exports
│   ├── spreadsheets/        # Excel/CSV files
│   ├── exports/            # Data exports from various systems
│   └── backups/            # Backup files
└── scripts/                # Utility scripts and tools
    ├── deploy/             # Deployment scripts
    └── maintenance/        # Maintenance utilities
```

---

## 🔗 External Platform Integrations

### **For Context & Data Access:**

#### **GitHub Integration**
- **Setup**: Place repository URLs in `docs/references/github-repos.md`
- **Usage**: I can help with code review, documentation, and deployment
- **Access Method**: Provide specific repository URLs when needed

#### **Google Workspace**
- **Gmail**: Share relevant email threads via forwarding or screenshots
- **Drive**: Export documents to local files for analysis
- **Sheets**: Download as Excel/CSV for processing in this environment
- **Apps Script**: Develop and test scripts locally, then deploy

#### **Pipedrive CRM**
- **Data Export**: Regular CSV exports for analysis
- **API Integration**: Develop integrations within this secure environment
- **Custom Fields**: Document field mappings in `docs/business-context/`

#### **Social Media Platforms**
- **Analytics Data**: Export performance data for analysis
- **Content Planning**: Develop strategies and schedules locally
- **Asset Management**: Store creative assets in organized folders

---

## 📋 Project Context Management

### **Business Context Location:**
Store company-specific information in `/workspace/docs/business-context/`:

```
business-context/
├── company-overview.md      # Silver Fox Marketing overview
├── client-profiles/         # Individual client information
├── service-offerings.md     # Current services and pricing
├── brand-guidelines.md      # Brand voice and visual guidelines
├── tools-and-systems.md     # Current tech stack and integrations
└── team-structure.md        # Team roles and responsibilities
```

### **Project Documentation:**
For individual projects, create structured briefs in `/workspace/docs/project-briefs/`:

```
project-briefs/
├── points-program-automation/
│   ├── requirements.md
│   ├── technical-specs.md
│   └── implementation-plan.md
├── social-media-campaigns/
│   ├── campaign-strategy.md
│   ├── content-calendar.md
│   └── performance-metrics.md
└── client-websites/
    ├── discovery-notes.md
    ├── design-requirements.md
    └── development-timeline.md
```

---

## ⚡ Quick Start Commands

### **Initialize New Project:**
```bash
# Create project structure
mkdir -p /workspace/projects/[project-name]/{src,docs,tests}
mkdir -p /workspace/docs/project-briefs/[project-name]

# Initialize with templates
cp /workspace/docs/templates/project-brief.md /workspace/docs/project-briefs/[project-name]/
```

### **Common Development Tasks:**
```bash
# Start development server
npm run dev

# Run tests
npm test

# Deploy to staging
./scripts/deploy/staging.sh

# Backup current work
./scripts/maintenance/backup.sh
```

---

## 🛠 Available Tools & Libraries

### **Pre-installed in Environment:**
- **Node.js & NPM** - JavaScript runtime and packages
- **Python 3** - Data analysis and automation
- **Git** - Version control
- **Curl** - API testing and data fetching
- **Vim** - Text editor for quick edits

### **Commonly Used Libraries:**
- **Google APIs** - Sheets, Drive, Gmail integration
- **Axios** - HTTP requests
- **Lodash** - Utility functions
- **Moment.js** - Date manipulation
- **Puppeteer** - Web scraping and automation

---

## 📊 Data Security & Privacy

### **Container Isolation Benefits:**
- ✅ Isolated from your NAS and sensitive systems
- ✅ No persistent storage of sensitive data
- ✅ Network isolation when needed
- ✅ Easy cleanup and reset capabilities

### **Best Practices:**
- Store sensitive credentials in environment variables
- Use `.env` files for configuration (never commit to git)
- Regular cleanup of temporary files
- Backup important work to secure external storage

---

## 📞 How to Work With Me

### **Project Initiation:**
1. **Provide Context**: Share relevant business context and project requirements
2. **Define Scope**: Clear objectives and deliverables
3. **Resource Access**: Specify what external data/systems I need to work with
4. **Timeline**: Project deadlines and milestones

### **Ongoing Collaboration:**
- **Progress Updates**: Regular check-ins on project status
- **Code Reviews**: I'll review and optimize your existing code
- **Problem Solving**: Bring technical challenges for collaborative solutions
- **Documentation**: I'll maintain clear documentation for all work

### **Communication Style:**
- Be specific about requirements and constraints
- Share examples when possible
- Ask questions if anything is unclear
- Provide feedback on proposed solutions

---

## 🚀 Current Project Priorities

### **Primary Focus: Technology Development**
1. **PipeDrive Integration** - 2-month transition currently underway for complete CRM automation
2. **Scraper System Rebuild** - Eliminating dependencies, cloud deployment for reliability  
3. **Mobile Tools Development** - VIN scanning, QR verification for installation team efficiency
4. **Order Form Integration** - Dynamic PipeDrive-embedded order processing system
5. **Business Intelligence Dashboard** - Executive dashboard for real-time business insights

### **Secondary Focus: Social Media Authority Development**  
1. **LotSherpa Authority Strategy** - 80% automotive industry thought leadership content
2. **Dual-Brand Authority Management** - Launch LotSherpa without disrupting Silver Fox operations
3. **Community Integration Content** - Position automotive expertise to elevate all business graphics

### **Strategic Goals:**
- **LotSherpa**: $2M revenue target, 50 new dealer relationships, geographic expansion
- **Silver Fox**: Maintain St. Louis market dominance while building automotive industry authority
- **Technology Platform**: Industry-leading automation creating competitive advantages

*Note: Individual social media tools, content strategies, and program development have dedicated folders with detailed context documents.*

---

## 📝 Notes & Reminders

### **Important Considerations:**
- Always test integrations in staging environment first
- Maintain backup copies of critical automation scripts
- Document all custom solutions for team knowledge sharing
- Regular security reviews of external integrations

### **Contact & Support:**
- **Primary User**: Silver Fox Marketing Team
- **Environment**: Containerized Claude Code Sandbox
- **Last Updated**: July 18, 2025
- **Version**: 1.0

---

## 🔄 Regular Maintenance

### **Weekly Tasks:**
- [ ] Review and organize project files
- [ ] Update documentation for completed work
- [ ] Test critical automations and integrations
- [ ] Backup important scripts and configurations

### **Monthly Tasks:**
- [ ] Security review of access credentials
- [ ] Performance optimization of running systems
- [ ] Update project priorities and roadmap
- [ ] Clean up temporary files and unused resources

---

*Ready to help you build, automate, and optimize your Silver Fox Marketing operations. What shall we work on today?*