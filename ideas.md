- modify chatmode: rename feasibility.md to 01_feasibility.md requirements.md to 02_requirements.md and design.md to 03_design.md tasks.md to 04_tasks.md
rename feasibility.md and tasks.md to 04_tasks.md
-add __IN_PROGRESS__ file tos pec after you start to work on the tasks
- add __DONE__ file to spec after you finish ALL tasks

## GitLab Flow Integration Ideas

### Templating Engine Approach (Analyzed but NOT Recommended)
**Concept**: Use Jinja2 templating engine to make chatmode files dynamic
- Convert all `.md` templates to `.j2` Jinja2 templates
- Add conditional logic: `{% if gitlab_flow_enabled %}...{% endif %}`
- CLI generates final `.md` files from templates at runtime
- Support dynamic includes and complex template logic

**Analysis Result**: ❌ REJECTED
- **Effort**: 2-3 weeks major refactor
- **Impact**: Breaking changes to ALL template files
- **Complexity**: Every test needs Jinja2 mocking
- **Risk**: Template syntax errors become runtime issues
- **Dependencies**: New Jinja2 dependency

**Better for**: Major version 2.0 architectural overhaul
**Not suitable for**: Focused GitLab Flow feature addition

### Option A: Simple Conditional Includes (CHOSEN APPROACH)
**Concept**: Use markdown comments and optional workflow files
- Keep main chatmode files static and simple
- Add markdown comments indicating optional GitLab Flow sections
- Create separate workflow files that users can reference when needed
- No templating engine, no breaking changes
- Clean separation between core workflow and git operations

**Benefits**:
- ✅ Zero breaking changes to existing templates
- ✅ Simple implementation (days not weeks)
- ✅ Easy to understand and maintain
- ✅ No new dependencies
- ✅ Works with existing template system

-default help command for improved-sdd
improved-sdd --help
