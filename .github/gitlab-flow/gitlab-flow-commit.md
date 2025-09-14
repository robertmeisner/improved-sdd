## Commit Phase Progress

After completing and approving this phase of the specification workflow, commit your progress to maintain version control and enable collaboration.

### Commit Changes

Run the following command to commit your current phase:

```bash
# Stage and commit phase completion
{COMMIT}
```

### Commit Message Templates

Use these conventional commit message formats for consistency:

#### Feasibility Phase
```
feat: Add feasibility assessment for {feature-name}

- Assess technical requirements and complexity
- Identify potential risks and mitigation strategies
- Estimate effort and resources needed
- Document recommendation and next steps
```

#### Requirements Phase
```
feat: Add requirements for {feature-name}

- Define user stories and acceptance criteria
- Specify success metrics and out-of-scope items
- Document functional and non-functional requirements
- Establish testing scenarios and edge cases
```

#### Design Phase
```
feat: Add design for {feature-name}

- Define system architecture and components
- Specify data models and API contracts
- Document security and performance considerations
- Plan testing strategy and rollback procedures
```

#### Tasks Phase
```
feat: Add implementation tasks for {feature-name}

- Break down design into actionable coding tasks
- Prioritize critical path and parallel work
- Estimate effort and identify dependencies
- Plan incremental development approach
```

#### Implementation Progress
```
feat: Implement {specific-task-name} for {feature-name}

- Complete task {task-number}: {task-description}
- Add comprehensive test coverage
- Update documentation and comments
- Validate against requirements
```

### Commit Best Practices

**✅ Good Commit Practices**:
- [ ] Descriptive commit message following conventional format
- [ ] Single logical change per commit
- [ ] All related files included
- [ ] Phase completely finished before committing

**📋 Incremental Progress Tracking**:
- Each spec phase gets its own commit
- Implementation tasks committed individually
- Progress visible through commit history
- Enables easy rollback if needed

**Next Phase**: Continue to next workflow phase or proceed with implementation tasks.
